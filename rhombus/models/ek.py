

from .core import *
from rhombus.lib.utils import get_dbhandler

@registered
class EK(BaseMixIn, Base):
    """ EK

        This class implements poor-man EnumeratedKeys.
    """

    __tablename__ = 'eks'

    key = Column(types.String(128), nullable=False)
    desc = Column(types.String(128), nullable=False)
    data = deferred(Column(types.Binary(), nullable=True))
    syskey = Column(types.Boolean, nullable=False, default=False)

    member_of_id = Column(types.Integer, ForeignKey('eks.id'), index=True)
    members = relationship('EK', order_by='EK.key',
                    backref=backref('member_of', remote_side= 'EK.id', uselist=False))

    group_id = Column(types.Integer, ForeignKey('groups.id'))
    group = relationship('Group', uselist=False)

    __table_args__ = ( UniqueConstraint('key', 'member_of_id'), {} )

    #cache = idcache()


    def __init__(self, key='', desc='',  data='', member_of_id=None, parent=None):
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
        return dict( id = self.id, key = self.key, desc = self.desc,
                    syskey = self.syskey, data = self.data,
                    lastuser = self.lastuser.as_dict() if self.lastuser else None,
                    group = self.group.name if self.group else None,
                    stamp = self.stamp,
                    members = [ m.as_dict() for m in self.members ] )


    @staticmethod
    def from_dict( d, update=False, dbsession=None):
        assert dbsession, 'Please provide dbsession'
    
        ek = EK()
        ek.key = d['key']
        ek.desc = d.get('desc', None)
        ek.data = d.get('data', None)
        ek.syskey = d.get('syskey', None)

        if update:
            db_ek = EK.search(ek.key, dbsession=dbsession)
            db_ek.update( ek )
        else:
            if ek.group:
                group_ek = EK.search(ek.group, dbsession=dbsession)
                ek.member_of_id = group_ek.id
            dbsession.add( ek )
            dbsession.flush()
            db_ek = ek

        return db_ek


    def data_from_json(self):
        if self.data:
            return json.loads( self.data.decode('UTF-8') )
        return None

    @staticmethod
    def _key(id, dbsession):
        key_pair = dbsession.get_key(id)
        if key_pair: return key_pair[0]

        ek = EK.get(id, dbsession)
        if ek:
            dbsession.set_key((ek.key, ek.member_of.key if ek.member_of else None), ek.id)
            return ek.key

        return None

    @staticmethod
    def _id(key, dbsession=None, grp=None, auto=False):
        """ key and grp is the key name (as string) """
        if dbsession is None:
            dbsession = get_dbhandler().session()
        id = dbsession.get_id((key, grp))
        if id: return id

        ek = EK.search(key, grp, dbsession)
        if not ek:
            if not auto:
                raise KeyError( "Key: %s is not found!" % key )
            if not grp:
                raise RuntimeError('EK: when set auto creation, group needs to be provided')
            group = EK.search(grp, dbsession=dbsession)
            ek = EK(key, '-', parent=group)
            dbsession.add( ek )
            dbsession.flush([ek])

        dbsession.set_key((ek.key, grp), ek.id)
        return ek.id


    @staticmethod
    def getid(key, dbsession, grp=None, auto=False):
        return EK._id(key, dbsession, grp, auto)

    @staticmethod
    def getids(keys, dbsession, grp=None, auto=False):
        return [ EK.getid(k, dbsession, grp, auto) for k in keys ]

    @staticmethod
    def getkey(id, dbsession):
        return EK._key(id, dbsession)

    @staticmethod
    def getkeys(ids):
        return [ EK.getkey(id) for id in ids ]


    @staticmethod
    def search(key, group=None, dbsession=None):
        assert dbsession, "Please provide dbsession!"
        assert group == None or type(group) == str, "group argument must be string or None"
        q = EK.query(dbsession).autoflush(False).filter( EK.key.ilike(key) )
        if group:
            q = q.filter( EK.member_of_id == EK._id(group, dbsession=dbsession) )
        r = q.all()
        if r: return r[0]
        return None

    @staticmethod
    def getmembers(grpname, dbsession):
        return EK.query(dbsession).filter( EK.member_of_id == EK._id(grpname, dbsession) )

    @staticmethod
    def get_members(grpname, dbsession):
        return EK.getmember( grpname, dbsession )

    def __repr__(self):
        return self.key

    @staticmethod
    def allparents(dbsession):
        parents = EK.query(dbsession).filter( EK.key.startswith('@') ).all()
        return [ (x.id, x.key) for x in parents ]

    @staticmethod
    def bulk_insert( alist, parent=None, syskey=False, dbsession=False ):
        """ [ ( '@IDENTIFIER', 'Identifiers', [ ( 'k1', 'd1'), ('k2', 'd2'), ... ] ), ... ] """
        assert dbsession, "FATAL ERROR - must provide dbsession arg"
        for item in alist:
            if type(item) == str:
                k = d = item
            else:
                (k, d) = item[:2]
            if d is None:
                # update/add members of this particular key, assuming the key already
                # exists in the database
                ek = EK.search( k, dbsession = dbsession )
                EK.bulk_insert( item[2], ek, syskey, dbsession = dbsession )
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
            dbsession.add( ek )
            if len(item) == 3:
                dbsession.flush()
                EK.bulk_insert( item[2], ek, syskey, dbsession = dbsession )


    @staticmethod
    def proxy(attrname, grpname, match_case=False, auto=False):
        def _getter(inst):
            _id = getattr(inst, attrname)
            #print("*** id is", _id, "for attr", attrname)
            dbsession = object_session(inst)
            if dbsession is None:
                dbsession = get_dbhandler().session()
            key = EK._key( getattr(inst, attrname), dbsession)
            if not match_case and key:
                return key.lower()
            return key
        def _setter(inst, value):
            #print("*** set attr", attrname)
            if not match_case: value = value.lower()
            dbsession = object_session(inst)
            if not dbsession and hasattr(inst, '_dbh_session_'):
                dbsession = getattr(inst, '_dbh_session_')
            setattr(inst, attrname, EK._id( value, dbsession, grpname, auto=auto) )
            #print("*** set attr", attrname, "with", getattr(inst, attrname))
        return property(_getter, _setter, doc=grpname)


    @staticmethod
    def dump(_out, query = None, dbsession=None):
        import yaml
        assert dbsession, "Please provide dbsession"
        if not query:
            query = EK.query(dbsession).filter( EK.member_of_id == None )
        yaml.safe_dump_all( (x.as_dict() for x in query), _out, default_flow_style = False )


    @staticmethod
    def load( _in ):
        import yaml
        

