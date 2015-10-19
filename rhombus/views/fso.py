
from rhombus.views import *

import shutil, os, re


def get_file_size(file):
    file.seek(0, 2) # Seek to the end of the file
    size = file.tell() # Get the position of EOF
    file.seek(0) # Reset the file position to the beginning
    return size


def save_file(destpath, filestorage, request):
    """ return (size, total) bytes written """

    fileobj = filestorage.file
    filesize = get_file_size(fileobj)
    filename = os.path.basename(filestorage.filename)

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
            with open(destpath, 'wb') as f:
                fileobj.seek(0, 0)
                shutil.copyfileobj(fileobj, f)
                size = get_file_size(f)

        if not end == size-1:
            raise RuntimeError('ERR - writing to file %s' % destpath)

        return (size, total)


@roles( PUBLIC )
def index(request):
    """ send the content of file to browser
    """

    path = request.matchdict.get('path', '')
    if not path:
        return error_page('ERR - Path not specified!')

    fso_file = FileOverlay.open(path)
    if not fso_file.check_permission(request.user, 'r'):
        return error_page('ERR - authorization error, permission denied.')

    return FileResponse( fso_file.abspath )
