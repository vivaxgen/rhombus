from .core import (Base, BaseMixIn, Column, types, ForeignKey, registered, deferred,
                   NoResultFound, object_session)
from .ek import EK

from rhombus.lib.utils import get_dbhandler
import mimetypes
import io


@registered
class FileAttachment(Base, BaseMixIn):
    """ FileAttachment

        This class implement general scheme for file attachment handling, which
        does not require fullpath or hierarchical arrangment and hence simpler than
        models.filemgr.File class.

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

    flags = Column(types.Integer, nullable=False, server_default='0')
    """ optional flags """

    __ek_fields__ = ['type', 'mimetype']

    def __repr__(self):
        return f'{self.__class__.__name__}(filename={self.filename}, size={len(self.bindata)})'

    def __str__(self):
        return self.filename

    def fp(self):
        if self.size == 0:
            return io.BytesIO(b'')
        return io.BytesIO(self.bindata)

    def update(self, d):

        if hasattr(d, 'filename') and hasattr(d, 'file'):
            # FieldStorageClass-like objects
            self.filename = d.filename
            buf = d.file.read()
            self.bindata = buf
            self.size = len(buf)
            self.mimetype = mimetypes.guess_type(self.filename)[0]

        elif isinstance(d, dict) or isinstance(d, FileAttachment):
            super().update(d)

        else:
            raise RuntimeError('fileattachment must be updated by either FieldStorage, dictionary, or itself')

        return self

    @staticmethod
    def proxy(attrname):
        """ attrname is the relationship to File """
        def _getter(inst):
            return getattr(inst, attrname)

        def _setter(inst, value):
            """ various value need to be considered """
            if value == b'':
                return None
            sess = object_session(inst) or get_dbhandler().session()
            file_instance = getattr(inst, attrname)
            if file_instance is None:
                file_instance = FileAttachment()
                sess.add(file_instance)
                setattr(inst, attrname, file_instance)
            file_instance.update(value)
            sess.flush([file_instance])

        return property(_getter, _setter, doc=attrname)

    def as_dict(self):
        raise NotImplementedError('this functionality has not been implemented')

# EOF
