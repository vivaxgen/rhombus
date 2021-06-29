__copyright__ = '''
stampmixin.py - Rhombus SQLAlchemy stamp mixin

(c) 2021 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

from sqlalchemy import types, Column, Sequence, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql.functions import current_timestamp, now

from rhombus.lib.utils import get_userid


class StampMixIn(object):
    """ StampMixIn

        This is base class for all object that needs id, lastuser_id and
        stamp attribute.
    """

    @declared_attr
    def id(cls):
        return Column(types.Integer,
                      Sequence('%s_seqid' % cls.__name__.lower(), optional=True),
                      primary_key=True)

    @declared_attr
    def lastuser_id(cls):
        return Column(types.Integer,
                      ForeignKey('users.id'),
                      default=get_userid,
                      onupdate=get_userid,
                      nullable=True)

    @declared_attr
    def lastuser(cls):
        return relationship('User', uselist=False, foreign_keys=[cls.lastuser_id])

    @declared_attr
    def stamp(cls):
        return Column(types.TIMESTAMP, nullable=False, default=current_timestamp(),
                      onupdate=now())
        ## this is reserved for big, incompatible update
        ## return Column(types.DateTime(timezone=True), nullable=False,
        ##        server_default=func.now(), server_onupdate=func.utc_timestamp())

    def __before_update__(self):
        # this is to force some database backend to change the values
        # during update
        session = object_session(self)
        if not session.before_update_event or getattr(self, 'ignore_before_update', False):
            return
        self.lastuser_id = get_userid()
        self.stamp = now()
