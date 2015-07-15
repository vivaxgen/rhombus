
from .core import *
from .ek import EK


@registered
class File(BaseMixIn, Base):
    """ File

        This class implement general scheme for file handling
    """

    __tablename__ = 'files'

    path = Column(types.String(128), nullable=False, unique=True)
    """ unique full path name for the file """

    type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    type = EK.proxy('type_id', '@FILETYPE')
    """ type of the file """

    parent_id = Column(types.Integer, ForeignKey('files.id'), nullable=True, index=True)
    """ parent id for hierarchical relationship """

    mimetype_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    mimetype = EK.proxy('mimetype_id', '@MIMETYPE')
    """ mimetype for this file """

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False,
                default = get_groupid)
    """ group_id for this file, default use user's primarygroup_id """

    bindata = Column(types.Binary, nullable=False, default=b'')
    """ actual data """

    permanent = Column(types.Boolean, nullable=False, default=False)
    """ whether this is permanent file or temporary file """

    acl = Column(types.Integer, nullable=False, default=0)
    """ acl follows basic UNIX permission model:
             0 ~ follow parent,
            -1 ~ group_id only
    """

    entries = relationship("File",

                        # cascade deletions
                        cascade="all",

                        # many to one + adjacency list - remote_side
                        # is required to reference the 'remote'
                        # column in the join condition.
                        backref=backref("parent", remote_side='File.id')

                        # entries will be represented as a dictionary
                        # on the "path" attribute.
                        #collection_class=attribute_mapped_collection('path'),
                    )



    @property
    def filename(self):
        if self.type == 'file/folder':
            return ''
        return self.path.rsplit('/',1)[1]

    @filename.setter
    def filename(self, filename):
        if self.type == 'file/folder':
            raise RuntimeError('cannot rename filename within folder object')
        self.path = self.path.rsplit('/',1)[0] + '/' + filename


    @staticmethod
    def search(path):
        try:
            return File.query().filter( File.path == path ).one()
        except NoResultFound:
            return None

    @staticmethod
    def save(ppath, filename, content, filetype='file/file',
                        mimetype=None, permanent = True):
        parent = File.search(ppath)
        if not parent:
            raise RuntimeError('Parent path not found: %s' % ppath)

        if not mimetype:
            mimetype = 'image/png' if filename.endswith('.png') else (
                    'image/jpg' if filename.endswith('.jpg') else (
                    'image/gif' if filename.endswith('.gif') else (
                    'application/pdf' if filename.endswith('.pdf') else
                    'application/octet-stream' )))

        fullpath = ppath + filename if not ppath.endswith('/') else ppath + '/' + filename

        file = File( path = fullpath, type = filetype, parent = parent,
                    mimetype = mimetype, permanent = permanent, bindata = content )

        return file


