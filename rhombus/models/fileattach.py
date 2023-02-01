from .core import (Base, BaseMixIn, Column, types, ForeignKey, registered, deferred,
                   NoResultFound, object_session)
from .ek import EK

from rhombus.lib.utils import get_dbhandler
from rhombus.lib.fileutils import get_file_size
from sqlalchemy import event
from pathlib import Path
import mimetypes
import shutil
import io


@registered
class FileAttachment(Base, BaseMixIn):
    """ FileAttachment

        This class implement general scheme for file attachment handling, which
        does not require fullpath or hierarchical arrangement and hence simpler than
        models.filemgr.File class.

        For big files, a mechanism to store the data as files in filesystems is also
        provided.

    """

    __tablename__ = 'fileattachments'

    filename = Column(types.String(64), nullable=False, server_default='')
    """ original file name """

    mimetype_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    mimetype = EK.proxy('mimetype_id', '@MIMETYPE', auto=True)
    """ mimetype for this file """

    size = Column(types.Integer, nullable=False, server_default='0')
    bindata = deferred(Column(types.LargeBinary, nullable=False, server_default=''))
    """ actual data """

    fullpath = Column(types.String(128), nullable=True, unique=True)
    """ path to actual file, hence must be unique to prevent overwriting """

    classtype = Column(types.Integer, nullable=False, server_default='0')
    """ for inheritance purposes """

    flags = Column(types.Integer, nullable=False, server_default='0')
    """ optional flags """

    __table_args__ = (
    )

    __mapper_args__ = {
        "polymorphic_on": classtype,
        "polymorphic_identity": 0,
    }

    __root_storage_path__ = None
    __maxdbsize__ = 1024 * 1024
    __maxsize__ = 250 * 1024 * 1024
    __subdir__ = 'attachments'
    """ max of 250M seems reasonable for attachment file """

    # __ek_fields__ = ['type', 'mimetype']

    def __repr__(self):
        return f'{self.__class__.__name__}(filename={self.filename}, size={len(self.bindata)})'

    def __str__(self):
        return self.filename

    def fp(self):
        if self.size == 0:
            return io.BytesIO(b'')
        elif self.fullpath is None:
            return io.BytesIO(self.bindata)
        elif self.fullpath:
            return open(self.get_fs_abspath(), 'rb')
        raise NotImplementedError('reading from filesystem has not been implemented')

    @classmethod
    def set_root_storage_path(cls, path):
        cls.__root_storage_path__ = Path(path) / cls.__subdir__

    @classmethod
    def set_max_dbsize(cls, size):
        cls.__maxdbsize__ = size

    def generate_fullpath(self):
        """ generate a new fullpath composed from self.id and filename """
        hex_id = f'{self.id:05x}'
        return Path(hex_id[-3:], f'{{{hex_id}}}-{self.filename}').as_posix()

    def save_from_stream(self, filename, stream):
        self.filename = filename
        self.mimetype = mimetypes.guess_type(self.filename)[0]
        self.size = get_file_size(stream)

        if self.size > self.__maxsize__:
            raise RuntimeError(f'Uploaded file exceeds max size of {self.__maxsize__} bytes')

        if self.size <= self.__maxdbsize__:
            self.fullpath = None
            self.bindata = stream.read()
        else:
            # update the content to actual file
            if self.id is None:
                object_session(self).flush([self])
            self.fullpath = self.generate_fullpath()
            destpath = self.get_fs_abspath()
            destpath.parent.mkdir(parents=True, exist_ok=True)
            with open(destpath, 'wb') as f:
                shutil.copyfileobj(stream, f)
                size = get_file_size(f)
            if not self.size == size:
                raise RuntimeError(f'ERR - incorrect file size during writing to file {destpath}')

    @classmethod
    def create_from_path(cls, fullpath, filename, session, mimetype=None, use_move=False,
                         func=None):
        """ func is a function to be called before file operation steps, with signature
            func(x) and x = newly created FileAttachment
        """

        fa = cls(filename=filename,
                 mimetype=mimetype or mimetypes.guess_type(filename)[0],
                 size=fullpath.stat().st_size)
        if func is not None:
            func(fa)
        session.add(fa)
        session.flush([fa])
        fa.fullpath = fa.generate_fullpath()
        destpath = fa.get_fs_abspath()
        destpath.parent.mkdir(parents=True, exist_ok=True)
        if use_move:
            shutil.move(fullpath, destpath)
        else:
            shutil.copyfile(fullpath, destpath)

        return fa

    def get_fs_abspath(self):
        """ return an absolute path for actual file """
        if self.__root_storage_path__ is None:
            raise AssertionError(f'set root storage path first by calling '
                                 f'{self.__class__.__name__}.set_root_storage_path()')
        return self.__root_storage_path__ / self.fullpath

    def update(self, d):

        if hasattr(d, 'filename') and hasattr(d, 'file'):
            # FieldStorageClass-like objects
            self.save_from_stream(d.filename, d.file)

        elif isinstance(d, dict) or isinstance(d, FileAttachment):
            super().update(d)

        elif hasattr(d, 'seek') and hasattr(d, 'name'):
            # already a stream object
            self.save_from_stream(d.name, d)

        else:
            raise RuntimeError('fileattachment must be updated by either FieldStorage, dictionary, or itself')

        return self

    @classmethod
    def proxy(cls, attrname):
        """ attrname is the relationship to File """
        def _getter(inst):
            return getattr(inst, attrname)

        def _setter(inst, value):
            """ various value need to be considered
                if value is b'' or empty bytes, no modification
                if value is None, remove the current FileAttachment, and set None
                if value is other than above, set the value properly
            """
            if value == b'':
                return None
            sess = object_session(inst) or get_dbhandler().session()

            # get the file instance referenced by attrname from the current instance
            file_instance = getattr(inst, attrname)

            if value is None:
                if file_instance is not None:
                    # if value is None but file instance exist, delete the file instance
                    setattr(inst, attrname, None)
                    sess.delete(file_instance)
                return

            # if value is valid, continue here

            if file_instance is None:
                # need to initialize file instance first
                file_instance = cls()
                sess.add(file_instance)
                setattr(inst, attrname, file_instance)

            # update & flush file instance
            file_instance.update(value)
            sess.flush([file_instance])

        return property(_getter, _setter, doc=attrname)

    def as_dict(self):
        raise NotImplementedError('this functionality has not been implemented')

    def clear(self):
        # removing file from fs storage
        if self.fullpath:
            Path(self.get_fs_abspath()).unlink(missing_ok=True)


# removal mechanism of file-based storage after attachment delete event
# there are 2 approaches:
# 1) removal of the actual file once an object is being deleted from session database
# 2) removal of all unreferenced files (with lastupdate < mtime < some threshold) by a periodic
#    sweeping process


__PENDING_FILES__ = []


#@event.listens_for(FileAttachment, 'after_delete')
def receive_after_delete(mapper, connection, target):
    global __PENDING_FILES__
    for t in target:
        sess = object_session(t)
        if sess not in __PENDING_FILES__:
            curr_list = __PENDING_FILES__[sess] = []
        if (fullpath := t.fullpath):
            curr_list.append(fullpath)


#@event.listens_for(FileAttachment, 'after_commit')
def receive_after_commit(session):
    global __PENDING_FILES__
    if session in __PENDING_FILES__:
        deleted_files = __PENDING_FILES__[session]
        del __PENDING_FILES__[session]
        for f in deleted_files:
            # removed files here
            pass

# EOF
