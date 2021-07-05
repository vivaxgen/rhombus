from .core import (Base, BaseMixIn, Column, types, ForeignKey, registered,
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
    mimetype = EK.proxy('mimetype_id', '@MIMETYPE')
    """ mimetype for this file """

    bindata = Column(types.LargeBinary, nullable=False, server_default='')
    """ actual data """

    flags = Column(types.Integer, nullable=False, server_default='0')
    """ optional flags """

    __ek_fields__ = ['type', 'mimetype']

    def fp(self):
        if not self.bindata or len(self.bindata) == 0:
            return io.BytesIO(b'')
        return io.BytesIO(self.bindata)

    def update(self, d):

        if hasattr(d, 'filename') and hasattr(d, 'file'):
            # FieldStorageClass-like objects
            self.filename = d.filename
            self.bindata = d.file.read()
            self.mimetype = mimetypes.guess_type(self.filename)[0]

        else:
            super().update(d)

        return self

    @staticmethod
    def proxy(attrname):
        """ attrname is the relationship to File """
        def _getter(inst):
            return getattr(inst, attrname)

        def _setter(inst, value):
            """ various value need to be considered """
            if value == b'': return None
            sess = object_session(inst) or get_dbhandler().session()
            file_instance = getattr(inst, attrname)
            if file_instance is None:
                file_instance = FileAttachment()
                sess.add(file_instance)
                setattr(inst, attrname, file_instance)
            file_instance.update(value)

        return property(_getter, _setter, doc=attrname)

# EOF
