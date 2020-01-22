
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

    posttype_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    posttype = EK.proxy('posttype_id', '@POSTTYPE')


    def update(self, obj):
        if isinstance(obj, dict):
            if 'user_id' in obj:
                self.user_id = obj['user_id']
            if 'group_id' in obj:
                self.group_id = obj['group_id']
            if 'posttype_id' in obj:
                self.posttype_id = obj['posttype_id']
            if 'title' in obj:
                self.title = obj['title']
            if 'content' in obj:
                self.content = obj['content']

            return self

        raise NotImplementedError('ERR: updating object uses dictionary object')



class Tag(Base):

    __tablename__ = 'tags'

    id = Column(types.Integer, primary_key=True)

    post_id = Column(types.Integer, ForeignKey('posts.id'), nullable=False, index=True)
    post = relationship(Post, uselist=False, backref=backref('tags', cascade='delete, delete-orphan'))

    tag_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False, index=True)
    tag = relationship(EK, uselist=False, foreign_keys=tag_id )

    user_id = Column(types.Integer, ForeignKey('users.id'))

    __table_args__ = (  UniqueConstraint('post_id', 'tag_id'), )


    @classmethod
    def sync_tags(cls, node_id, tag_ids, user_id = None, session = None):
        # synchronize node_id and tag_ids

        # check sanity
        assert type(node_id) == int
        for id in tag_ids:
            if type(id) != int:
                raise RuntimeError('FATAL ERR: tag_ids must contain ony integers')

        # check user_id first
        if not user_id:
            user_id = get_userid()

        if not session:
            session = get_dbhandler().session()

        tags = cls.query(session).filter(cls.node_id == node_id)
        in_sync = []
        for tag in tags:
            if tag.tag_id in tag_ids:
                in_sync.append( tag.tag_id )
            else:
                # remove this tag
                session.delete(tag)

        print(in_sync)
        for tag_id in tag_ids:
            if tag_id in in_sync: continue
            print('add %d' % tag_id)
            cls.add_tag(node_id, tag_id, user_id, session)


    @classmethod
    def add_tag(cls, node_id, tag_id, user_id, session):
        assert type(tag_id) == int

        if not session:
            session = get_dbhandler().session()
        if type(node_id) == int:
            tag = cls(node_id = node_id, tag_id = tag_id, user_id = user_id)
        else:
            tag = cls(node = node_id, tag_id = tag_id, user_id = user_id)
        session.add(tag)


    @classmethod
    def remove_tag(cls, node_id, tag_id, user_id, session):
        tag = cls.query().filter(cls.node_id == node_id, cls.tag_id == tag_id).one()
        session.delete(tag)