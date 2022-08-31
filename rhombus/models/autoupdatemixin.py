__copyright__ = '''
autoupdatemixin.py - Rhombus SQLAlchemy stamp mixin

(c) 2021 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

from sqlalchemy import Column, event
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import mapper
from sqlalchemy.orm.session import object_session

from rhombus.lib.utils import cerr
from rhombus.lib import roles as r

from itertools import chain


class AutoUpdateMixIn(object):

    # the following variables has to be set manually for each subclass

    # fields that are excluded from AutoUpdateMixIn value-update mechanism
    __excluded_fields__ = {'id', }

    # managing roles can manage this object regardless of ownership or groups
    __managing_roles__ = {r.SYSADM, r.DATAADM}

    # modifying roles can manage this object with ownership/group requirement
    __modifying_roles__ = __managing_roles__

    # the following variables will be set automatically after all mappers have
    # been configured

    # __plain_fields__ contains a list of SQL column names that directly
    # hold values
    __plain_fields__ = None

    # __nullable_fields__ contains a list of SQL column names that are
    # nullable plain fields (as such, a subset of __plain_fields__)
    __nullable_fields__ = None

    # __ek_fields__ contains the names of proxies of any plain fields
    # that relate to EK key
    __ek_fields__ = []

    # __rel_fields__ contains all relationship fields
    __rel_fields__ = None

    # __fk_fields__ holds foreign_keys fields connected to rel fields
    __fk_fields__ = None

    # __ek_metainfo__ holds meta information for each EK fields
    __ek_metainfo__ = None
    __aux_fields__ = None

    # __init_funcs__ holds functions to be invoked during object instance creation, eg. MyClass()
    __init_funcs__ = None

    @classmethod
    def add_init_funcs(cls, *args):
        if cls.__init_funcs__ is None:
            cls.__init_funcs__ = args
        else:
            cls.__init_funcs__.extend(args)

    def __init__(self, *args, **kwargs):
        """ *args and **kwargs is just for placeholders """
        super().__init__(*args, **kwargs)
        if self.__init_funcs__ is not None:
            for fn in self.__init_funcs__:
                fn(self)

    def update(self, obj):
        if isinstance(obj, dict):
            self.update_fields_with_dict(obj)
            self.update_ek_with_dict(obj)
        else:
            self.update_fields_with_object(obj)
        return self

    def serialized_code(self):
        raise NotImplementedError()

    @classmethod
    def can_modify(cls, user):
        raise NotImplementedError()

    @classmethod
    def bulk_load(cls, a_list, dbh, with_flush=False):
        """ bulk load from a list of dictionary object """
        dbsess = dbh.session()
        c = 0
        for a_dict in a_list:
            an_obj = cls.from_dict(a_dict, dbh)
            if with_flush:
                dbsess.flush([an_obj])
            cerr(f'[I - uploaded {cls.__name__}: {str(an_obj)}]')
            c += 1
        cerr(f'[I - {cls.__name__} uploaded: {c}]')

    @classmethod
    def bulk_dump(cls, dbh, q=None):
        """bulk dump either all objects or from q"""
        q = q or cls.query(dbh.session())
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

    def __json__(self, request):
        return self.as_dict()

    def update_fields_with_dict(self, a_dict, fields=None, exclude=None, additional_fields={}):
        fields = set(fields or self.get_plain_fields()) | set(additional_fields)
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

    def update_fields_with_object(self, an_obj, fields=None, exclude=None, additional_fields=[]):
        fields = (fields or self.get_plain_fields()) + additional_fields
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
                setattr(self, f, a_dict[f])
                continue
                f_ = f + '_id'
                if not hasattr(self, f_):
                    raise AttributeError(f_)
                cerr(f'setting for {f}')
                setattr(self, f_, dbh.EK.getid(a_dict[f], session))

    def create_dict_from_fields(self, fields=None, exclude=None):
        fields = fields or (
            (self.get_plain_fields() | set(self.__ek_fields__) | self.get_rel_fields()) - self.get_fk_fields())
        d = {}
        for f in fields:
            if exclude and f in exclude:
                continue
            if (val := getattr(self, f)) is not None:
                if isinstance(val, AutoUpdateMixIn):
                    d[f] = str(val)
                else:
                    d[f] = val
        return d

    def any_modified(self, a_dict, fields):
        """return True if any field is modified"""
        for f in fields:
            if v := a_dict.get(f, None):
                if v != getattr(self, f):
                    return True
        else:
            return False

    def all_modified(self, a_dict, fields):
        """return True if all fields are modified"""
        return self.some_modified(a_dict, fields, len(fields))

    def some_modified(self, a_dict, fields, threshold):
        """ return True if at least threshold modified"""
        c = 0
        for f in fields:
            if v := a_dict.get(f, None):
                if v != getattr(self, f):
                    c += 1
        return c >= threshold

    @classmethod
    def get_plain_fields(cls):
        return cls.__plain_fields__

    @classmethod
    def get_nullable_fields(cls):
        return cls.__nullable_fields__

    @classmethod
    def get_rel_fields(cls):
        return cls.__rel_fields__

    @classmethod
    def get_fk_fields(cls):
        return cls.__fk_fields__

    @classmethod
    def get_ek_metainfo(cls):
        return cls.__ek_metainfo__

    @classmethod
    def _get_all_subclasses(cls):
        """ return a generator that yield subclasses recursively """
        for subclass in cls.__subclasses__():
            yield from subclass._get_all_subclasses()
            yield subclass

    @classmethod
    def get_all_subclasses(cls):
        """ return a set of all subclasses of cls """
        return set(cls._get_all_subclasses())


@event.listens_for(mapper, 'after_configured')
def configure_autoupdatemixin_fields():
    # set all custom fields of AutoUpdateMixIn subclasses
    # after all mappers have been configured

    for cls in AutoUpdateMixIn.get_all_subclasses():

        # check if cls is not plain type class
        if type(cls) is type:
            cerr(f'skipping {cls} [{type(cls)}]')
            continue
        else:
            cerr(f'configuring {cls} [{type(cls)}]')

        # reset first
        cls.__plain_fields__ = []
        cls.__nullable_fields__ = []
        cls.__ek_fields__ = set()

        # set __plain_fields__ and __nullable_fields__

        for c in inspect(cls).c:
            if not isinstance(c, Column):
                continue
            if c.name in cls.__excluded_fields__:
                continue
            cls.__plain_fields__.append(c.name)
            if c.nullable:
                cls.__nullable_fields__.append(c.name)
        cls.__plain_fields__ = set(cls.__plain_fields__)
        cls.__nullable_fields__ = set(cls.__nullable_fields__)

        # set __ek_fields__

        #for key, attribute in vars(cls).items():
        for key in dir(cls):
            attribute = getattr(cls, key)
            if type(attribute) is property:
                if getattr(attribute, 'fget').__name__ == '_ek_proxy_getter':
                    cls.__ek_fields__.add(key)
        cerr(f'Configuring {cls} with __ek_fields__ = {cls.__ek_fields__}')

        # set __ek_metainfo, __rel_fields__ and __fk_fields__

        cls.__ek_metainfo__ = {}
        rels = inspect(cls).relationships
        cls.__rel_fields__ = set(r.key for r in rels if r.key not in cls.__excluded_fields__)
        cls.__fk_fields__ = set(c.name
                                for c in chain.from_iterable(r.local_columns for r in rels)
                                if c.name not in cls.__excluded_fields__
                                )
        for ekf in cls.__ek_fields__:
            cls.__ek_metainfo__[ekf] = getattr(cls, ekf).__doc__.split()[1:]
        cls.__fk_fields__ |= set(item[0] for item in cls.__ek_metainfo__.values())


# end of file
