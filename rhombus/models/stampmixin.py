__copyright__ = '''
stampmixin.py - Rhombus SQLAlchemy stamp mixin

(c) 2021 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

from sqlalchemy import types, Column, ForeignKey, Identity
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql.functions import now

from rhombus.lib.utils import get_userid

__version__ = '20210629'


class StampMixIn(object):
    """ StampMixIn

        This is base class for all object that needs id, lastuser_id and
        stamp attribute.
    """

    @declared_attr
    def id(cls):
        return Column(types.Integer, Identity(), primary_key=True)

    @declared_attr
    def create_time(cls):
        return Column(types.DateTime(timezone=True), nullable=False, server_default=now())

    @declared_attr
    def lastuser_id(cls):
        return Column(types.Integer,
                      ForeignKey('users.id', use_alter=True),
                      default=get_userid,
                      onupdate=get_userid,
                      nullable=True)

    @declared_attr
    def lastuser(cls):
        return relationship('User', uselist=False, foreign_keys=[cls.lastuser_id])

    @declared_attr
    def stamp(cls):
        # we use DateTime instead of TIMESTAMP to get consistent behaviour across different
        # RDBM systems
        return Column(types.DateTime(timezone=True), nullable=False,
                      server_default=now(), onupdate=now())

    def __before_update__(self):
        # this is to force some database backend to change the values
        # during update
        session = object_session(self)
        if not session.before_update_event or getattr(self, 'ignore_before_update', False):
            return
        self.lastuser_id = get_userid()
        self.stamp = now()

# end of file
