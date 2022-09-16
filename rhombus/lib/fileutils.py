
import pathlib
import re
import shutil


def get_file_size(fileobj):
    """ given a file object, return the size of the file """
    fileobj.seek(0, 2)  # Seek to the end of the file
    size = fileobj.tell()  # Get the position of EOF
    fileobj.seek(0)  # Reset the file position to the beginning
    return size


def save_file(destpath, filestorage, request):
    """ save a chunk (or whole) of file referred by filestorage field from request
        and return (size, total) bytes written
    """

    fileobj = filestorage.file
    filesize = get_file_size(fileobj)
    filename = pathlib.Path(filestorage.filename).name

    # check whether this is a chunked file or whole file

    if 'Content-Range' not in request.headers:
        # whole file
        with open(destpath, 'wb') as f:
            fileobj.seek(0, 0)
            shutil.copyfileobj(fileobj, f)
            size = get_file_size(f)

        if not filesize == size:
            raise RuntimeError('ERR - writing to file %s' % destpath)

        return (size, size)

    else:
        # chunked file
        content_range = request.headers['Content-Range']
        # parse content_range
        mo = re.match(r'\D+\W+(\d+)-(\d+)\/(\d+)', content_range)
        values = mo.groups()
        if len(values) == 3:
            begin, end, total = tuple( int(x) for x in values )
        else:
            raise RuntimeError('ERR - unparseable Content-Range header!')

        if begin > 0:
            # we just continue to append file
            with open(destpath, 'r+b') as f:
                current_size = get_file_size(f)
                if not begin == current_size:
                    raise RuntimeError('Subsequent chunk does not match!')
                f.seek(0, 2)
                fileobj.seek(0, 0)
                shutil.copyfileobj(fileobj, f)
                size = get_file_size(f)

        else:
            # create a new file
            with open(destpath, 'wb') as f:
                fileobj.seek(0, 0)
                shutil.copyfileobj(fileobj, f)
                size = get_file_size(f)

        if not end == size - 1:
            raise RuntimeError('ERR - writing to file %s' % destpath)

        return (size, total)

# EOF
