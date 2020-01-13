
from rhombus.models.core import *
from rhombus.models.ek import *

class Post(Base, BaseMixIn):
    """
        BaseMixIn ensures the id, lastuser_id and stamp
    """

    __tablename__ = 'posts'

    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    title = Column(types.String(256), nullable=False, server_default='')
    content = Column(types.String(2048), nullable=False, server_default='')


    def update(self, obj):
        if isinstance(obj, dict):
            super().update( obj )
            if 'user_id' in obj:
                self.user_id = obj['user_id']
            if 'group_id' in obj:
                self.group_id = obj['group_id']
            if 'title' in obj:
                self.title = obj['title']
            if 'content' in obj:
                self.content = obj['content']

        raise NotImplementedError('ERR: updating object uses dictionary object')


