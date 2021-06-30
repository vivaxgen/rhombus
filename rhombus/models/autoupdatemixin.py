__copyright__ = '''
stampmixin.py - Rhombus SQLAlchemy stamp mixin

(c) 2021 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

from sqlalchemy import Column
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.session import object_session


class AutoUpdateMixIn(object):

    # this is for caching field/column lookup

    # plain fields are fields that directly hold values, and automatically
    # filled by parsing all columns when the get_plain_fields() is called
    __plain_fields__ = None

    # nullable fields are plain fields that can have null value, and
    # automatically filled when get_nullable_fields() is called, as such
    # nullable fields are subset of plain fields
    __nullable_fields__ = None

    # ek fields are proxies of any plain fields that relate to EK key, and
    # the variable needs to be filled manually
    __ek_fields__ = []

    # rel fields are all relationship parsed automatically when
    # get_rel_fields() is called
    __rel_fields__ = None

    # auxiliary fields
    __aux_fields__ = None

    __excluded_fields__ = {'id', }

    @classmethod
    def bulk_load(cls, a_list, dbh):
        """ bulk load from a list of dictionary object """
        objs = [cls.from_dict(d, dbh) for d in a_list]
        dbh.session().flush(objs)

    @classmethod
    def bulk_dump(cls, dbh):
        q = cls.query(dbh.session())
        return [obj.as_dict() for obj in q]

    @classmethod
    def from_dict(cls, a_dict, dbh):
        """ load and add from a dict """
        obj = cls()
        with dbh.session().no_autoflush:
            dbh.session().add(obj)
            obj.update(a_dict)

        return obj

    def as_dict(self, exclude=None):
        d = self.create_dict_from_fields(exclude=exclude)
        # check if lastuser field from stampmixin exists
        if 'lastuser_id' in d and self.lastuser:
            d['lastuser'] = self.lastuser.login
        return d

    def update_fields_with_dict(self, a_dict, fields=None, exclude=None):
        fields = fields or self.get_plain_fields()
        nullable_fields = self.get_nullable_fields()
        for f in fields:
            if exclude and f in exclude:
                continue
            if f in a_dict:
                if not hasattr(self, f):
                    raise AttributeError(f)
                if f in nullable_fields:
                    value = a_dict.get(f)
                    if value is None or value == '':
                        continue
                setattr(self, f, a_dict.get(f))

    def update_fields_with_object(self, an_obj, fields=None, exclude=None):
        fields = fields or self.get_plain_fields()
        for f in fields:
            if exclude and f in exclude:
                continue
            if hasattr(an_obj, f):
                if not hasattr(self, f):
                    raise AttributeError(f)
                setattr(self, f, getattr(an_obj, f))

    def update_ek_with_dict(self, a_dict, fields=None, dbh=None):
        fields = fields or self.__ek_fields__
        session = dbh.session() if dbh else object_session(self)
        for f in fields:
            if f in a_dict:
                f_ = f + '_id'
                if not hasattr(self, f_):
                    raise AttributeError(f_)
                setattr(self, f_, dbh.EK.getid(a_dict[f], session))

    def create_dict_from_fields(self, fields=None, exclude=None):
        fields = fields or (self.get_plain_fields() + self.__ek_fields__)
        d = {}
        for f in fields:
            if exclude and f in exclude:
                continue
            d[f] = getattr(self, f)
        return d

    @classmethod
    def get_plain_fields(cls):
        if cls.__plain_fields__ is None:
            cls.__plain_fields__ = []
            cls.__nullable_fields__ = []
            for c in inspect(cls).c:
                if not isinstance(c, Column):
                    continue
                if c.name in cls.__excluded_fields__:
                    continue
                cls.__plain_fields__.append(c.name)
                if c.nullable:
                    cls.__nullable_fields__.append(c.name)
        return cls.__plain_fields__

    @classmethod
    def get_nullable_fields(cls):
        if cls.__nullable_fields__ is None:
            cls.get_plain_fields()
        return cls.__nullable_fields__

    @classmethod
    def get_rel_fields(cls):
        if cls.__rel_fields__ is None:
            rels = inspect(cls).relationships
            cls.__rel_fields__ = list(r.key for r in rels if r.key not in cls.__excluded_fields__)
        return cls.__rel_fields__

# end of file
