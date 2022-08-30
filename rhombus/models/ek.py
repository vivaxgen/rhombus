__copyright__ = '''
ek.py - Rhombus SQLAlchemy enumerated key (EK) module

(c) 2021 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

from .core import (registered, Column, types, Base, BaseMixIn, object_session, column_property,
                   ForeignKey, deferred, Identity, relationship, UniqueConstraint, backref,
                   column_mapped_collection, association_proxy, Table, metadata, and_,
                   NoResultFound)

from rhombus.lib.utils import get_dbhandler, cerr

import json
import yaml


@registered
class EK(BaseMixIn, Base):
    """ EK

        This class implements poor-man EnumeratedKeys.
    """

    __tablename__ = 'eks'

    key = Column(types.String(128), nullable=False)
    desc = Column(types.String(128), nullable=False)
    data = deferred(Column(types.LargeBinary(), nullable=True))
    syskey = Column(types.Boolean, nullable=False, default=False)

    member_of_id = Column(types.Integer, ForeignKey('eks.id'), index=True)
    members = relationship('EK', order_by='EK.key',
                           backref=backref('member_of', remote_side='EK.id', uselist=False))

    group_id = Column(types.Integer, ForeignKey('groups.id'))
    group = relationship('Group', uselist=False)

    __table_args__ = (UniqueConstraint('key', 'member_of_id'), {})

    def __init__(self, key='', desc='', data='', member_of_id=None, parent=None):
        self.key = key
        self.desc = desc
        if member_of_id:
            self.member_of_id = member_of_id
        if parent:
            self.member_of_id = parent.id
        if data:
            self.data = data

    def update(self, obj):
        self.key = obj.key
        self.desc = obj.desc
        self.syskey = obj.syskey
        self.data = obj.data
        if obj.member_of_id is not None:
            self.member_of_id = obj.member_of_id

    def as_dict(self):
        d = super().as_dict()
        d['group'] = self.group.name if self.group else None
        d['members'] = [m.as_dict() for m in self.members]
        return d
        return dict(id=self.id, key=self.key, desc=self.desc,
                    syskey=self.syskey, data=self.data,
                    lastuser=self.lastuser.as_dict() if self.lastuser else None,
                    group=self.group.name if self.group else None,
                    stamp=self.stamp,
                    members=[m.as_dict() for m in self.members])

    @staticmethod
    def from_dict(d, dbh=None, update=False):
        assert dbh, 'Please provide dbhandler'

        dbsession = dbh.session()
        ek = EK()
        ek.key = d['key']
        ek.desc = d.get('desc', None)
        ek.data = d.get('data', None)
        ek.syskey = d.get('syskey', None)

        db_ek = EK.search(ek.key, group=d.get('member_of', None), dbsession=dbsession)
        if db_ek:
            if update:
                db_ek.update(ek)
        else:
            dbsession.add(ek)
            dbsession.flush()
            db_ek = ek

        for m in d.get('members', []):
            m_ek = EK.from_dict(m, dbh, update)
            m_ek.member_of = db_ek

        return db_ek

        if update:
            db_ek = EK.search(ek.key, dbsession=dbsession)
            db_ek.update(ek)
        else:
            if ek.group:
                group_ek = EK.search(ek.group, dbsession=dbsession)
                ek.member_of_id = group_ek.id
            dbsession.add(ek)
            dbsession.flush([ek])
            db_ek = ek

        return db_ek

    def data_from_json(self):
        if self.data:
            return json.loads(self.data.decode('UTF-8'))
        return None

    @staticmethod
    def _key(id, dbsession):
        key_pair = dbsession.get_key(id)
        if key_pair:
            return key_pair[0]

        ek = EK.get(id, dbsession)
        if ek:
            dbsession.set_key((ek.key, ek.member_of.key if ek.member_of else None), ek.id)
            return ek.key

        return None

    @staticmethod
    def _id(key, dbsession=None, grp=None, auto=False):
        """ key and grp is the key name (as string) """
        assert grp or key[0] == '@'
        if dbsession is None:
            dbsession = get_dbhandler().session()
        id = dbsession.get_id((key, grp))
        if id:
            return id

        ek = EK.search(key, grp, dbsession)
        if not ek:
            if not auto:
                raise KeyError("Key: %s/%s is not found and auto is False!" % (key, grp))
            if not grp:
                raise RuntimeError('EK: when set auto creation, group needs to be provided')
            group = EK.search(grp, dbsession=dbsession)
            ek = EK(key, '-', parent=group)
            dbsession.add(ek)
            dbsession.flush([ek])

        dbsession.set_key((ek.key, grp), ek.id)
        return ek.id

    @staticmethod
    def getid(key, dbsession, grp=None, auto=False):
        return EK._id(key, dbsession, grp, auto)

    @staticmethod
    def getids(keys, dbsession, grp=None, auto=False):
        return [EK.getid(k, dbsession, grp, auto) for k in keys]

    @staticmethod
    def getkey(id, dbsession):
        return EK._key(id, dbsession)

    @staticmethod
    def getkeys(ids):
        return [EK.getkey(id) for id in ids]

    @staticmethod
    def search(key, group=None, dbsession=None):
        assert dbsession, "Please provide dbsession!"
        assert group is None or type(group) == str or isinstance(group, EK), "group argument must be string, None or instance of EK"
        q = EK.query(dbsession).autoflush(False).filter(EK.key.ilike(key))
        if group:
            if type(group) == str:
                q = q.filter(EK.member_of_id == EK._id(group, dbsession=dbsession))
            else:
                q = q.filter(EK.member_of_id == group.id)
        r = q.all()
        if r:
            return r[0]
        return None

    @staticmethod
    def getmembers(grpname, dbsession):
        return EK.query(dbsession).filter(EK.member_of_id == EK._id(grpname, dbsession))

    @staticmethod
    def get_members(grpname, dbsession):
        return EK.getmember(grpname, dbsession)

    def __repr__(self):
        return self.key

    @staticmethod
    def allparents(dbsession):
        parents = EK.query(dbsession).filter(EK.key.startswith('@')).all()
        return [(x.id, x.key) for x in parents]

    @staticmethod
    def bulk_update(alist, parent=None, syskey=False, dbsession=False):
        """ [ ( '@IDENTIFIER', 'Identifiers', [ ( 'k1', 'd1'), ('k2', 'd2'), ... ] ), ... ] """
        assert dbsession, "FATAL ERROR - must provide dbsession arg"

        for item in alist:

            # check item, if this is a string then set k & d as the item
            # otherwise set k & d according to the item
            if type(item) == str:
                k = d = item
            else:
                (k, d) = item[:2]

            if d is None:
                # update/add members of this particular key, assuming the key already
                # exists in the database
                ek = EK.search(k, dbsession=dbsession)
                EK.bulk_update(item[2], ek, syskey, dbsession=dbsession)
                continue
            if type(d) == list:
                d, data = d[0], d[1]
            else:
                data = None
            if parent:
                ek = EK(k, d, parent=parent)
            else:
                ek = EK(k, d)
            if data:
                if type(data) is str:
                    ek.data = data.encode('UTF-8')
                else:
                    ek.data = data
            db_ek = EK.search(k, dbsession=dbsession, group=parent.key if parent else None)
            if not db_ek:
                dbsession.add(ek)
            else:
                cerr('Trying to update: %s/%s' % (ek.key, parent.key if parent else ''))
            if len(item) == 3:
                dbsession.flush()
                EK.bulk_update(item[2], ek, syskey, dbsession=dbsession)

    bulk_insert = bulk_update

    @staticmethod
    def proxy(attrname, grpname, match_case=False, auto=False, default=None):
        """
            attrname: the field name used in the corresponding class for holding the EK value
            grpname: the group name for the EK values
            match_case: whether to use case-sensitive string match
            auto: whether to automatically store a new value to EK database
            default: use this default value when None is given
        """

        def _ek_proxy_getter(inst):
            _id = getattr(inst, attrname)
            # print("*** id is", _id, "for attr", attrname)
            dbsession = object_session(inst)
            if dbsession is None:
                dbsession = get_dbhandler().session()
            key = EK._key(getattr(inst, attrname), dbsession)
            if not match_case and key:
                return key.lower()
            return key

        def _ek_proxy_setter(inst, value):
            # print("*** set attr", attrname)
            if value is None and default is not None:
                value = default
            if not match_case:
                value = value.lower()
            dbsession = object_session(inst)
            if not dbsession and hasattr(inst, '_dbh_session_'):
                dbsession = getattr(inst, '_dbh_session_')
            setattr(inst, attrname, EK._id(value, dbsession, grpname, auto=auto))
            # print("*** set attr", attrname, "with", getattr(inst, attrname))

        return property(_ek_proxy_getter, _ek_proxy_setter, doc=f'EK.proxy {attrname} {grpname}')

    @staticmethod
    def dump(_out, query=None, dbsession=None):
        assert dbsession, "Please provide dbsession"
        if not query:
            query = EK.query(dbsession).filter(EK.member_of_id is None)
        yaml.safe_dump_all((x.as_dict() for x in query), _out, default_flow_style=False)

    @classmethod
    def bulk_dump_xxx(cls, dbh, query=None):
        if not query:
            query = cls.query(dbh.session()).filter(cls.member_of_id is None)
        return [obj.as_dict() for obj in query]

    @classmethod
    def bulk_load_XXX(cls, a_list, dbh, with_flush=None):
        session = dbh.session()
        for item in a_list:
            cls.from_dict(item, dbsession=session)

    @staticmethod
    def load(_in):
        import yaml

# end of file
