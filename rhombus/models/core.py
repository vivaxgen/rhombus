__copyright__ = '''
core.py - Rhombus SQLAlchemy core objects

(c) 2011 - 2015 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

import logging

log = logging.getLogger(__name__)

__version__ = '20150216'


# essential import from sqlalchemy

from sqlalchemy import and_, or_, schema, types, MetaData, Sequence, Column, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship, backref, dynamic_loader, deferred
from sqlalchemy.orm.collections import column_mapped_collection, attribute_mapped_collection
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.functions import current_timestamp, now
from sqlalchemy.dialects.postgresql import base as pg

import uuid, json, yaml, copy
import transaction
import pickle
import threading

from .meta import get_base, get_dbsession, get_datalogger, RhoSession

#from pylons import session as tylons_session

# global variables

Base = get_base()
dbsession = get_dbsession()
metadata = Base.metadata
func_userid = None
func_groupid = None


# global function

def set_func_userid( func ):
    global func_userid
    func_userid = func

def get_userid():
    if func_userid:
        return func_userid()
    raise RuntimeError('ERR: get_userid() has not been set')


def set_func_groupid( func ):
    global func_groupid
    func_groupid = func

def get_groupid():
    if func_groupid:
        return func_groupid()
    return None


# create universal UUID

class UUID(types.TypeDecorator):
    name = 'rhombus.eijkman.go.id'
    impl = types.BLOB

    def __init__(self):
        types.TypeDecorator.__init__(self, length=16)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(types.BLOB(self.impl.length))
        else:
            return dialect.type_descriptor(pg.UUID())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            return value.bytes

    @staticmethod
    def _coerce(value):
        if value and not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(value)

            except (TypeError, ValueError):
                value = uuid.UUID(bytes=value)

        return value

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, uuid.UUID):
            value = self._coerce(value)

        if dialect.name == 'postgresql':
            return str(value)

        return value.bytes #if self.binary else value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if dialect.name == 'postgresql':
            if isinstance(value, uuid.UUID):
                return value
        else:
            return uuid.UUID(bytes=value)

    @classmethod
    def new(cls):
        return uuid.uuid3(uuid.NAMESPACE_URL, cls.name)


# create JSON column
# XXX: may be more appropriate to create a dict-based object that will serialize to JSON?

null = object()

class JSONCol(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        if value is null:
            value = None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

    def copy_value(self, value):
        return copy.deepcopy(value)

# create YAML column
#

null = null

class YAMLCol(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        if value is null:
            value = None
        return yaml.dump(value, default_flow_style=True)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return yaml.load(value, yaml.SafeLoader)

    def copy_value(self, value):
        return copy.deepcopy(value)


#
# class registration
#

class ClassRegistry(object):
    """
        use application/x-python-pickle

        please make sure that sync() & update_table() methods are not called
        if data logger is not used
    """

    def __init__(self):
        self._classes = {}
        self._by_class = {}
        self._by_id = {}

    def register(self, cls):
        if hasattr(cls, '__typeid__'):
            if cls.__typeid__ == -1: return
        self._classes[cls.lowername()] = cls
        cls.__typeid__ = None

    def sync(self):

        assert get_datalogger(), "ERROR: ClassRegistry.sync() should not be called!"

        log.info("Synchronizing class table registry...")

        try:
            log.info('Reading class registry...')
            class_table = SysReg.getdata('__class_table__')
            if class_table == None:
                raise NoResultFound
            last_id = -1
            for cls_name, cls_id in class_table.items():
                try:
                    cls = self._classes[cls_name]
                    self._by_class[cls] = cls_id
                    self._by_id[cls_id] = cls
                    cls.__typeid__ = cls_id
                    del self._classes[cls_name]
                except KeyError:
                    log.info('Removed class: %s [%d]' % (cls_name, cls_id))
                if cls_id > last_id:
                    last_id = cls_id

            if self._classes:
                class_table = self.update_table(class_table, last_id + 1)
                SysReg.setdata('__class_table__', 'text/json', class_table)
                dbsession.flush()
                transaction.manager.commit()


        except NoResultFound:
            log.info('Initialize class registry...')
            class_table = self.update_table()
            SysReg.setdata('__class_table__', 'text/json', class_table)
            transaction.manager.commit()

        except OperationalError:
            log.info('WARN: SysReg has not been initialized.')


    def get_id(self, cls):
        return self._by_class[cls]

    def get_class(self, id):
        return self._by_id[id]

    def update_table(self, class_table = {}, nextid = 1):

        assert get_datalogger(), "ERROR: ClassRegistry.update_table() should not be called!"

        for cls_name, cls in self._classes.items():
            class_table[cls_name] = nextid
            self._by_class[cls] = nextid
            self._by_id[nextid] = cls
            cls.__typeid__ = nextid
            nextid += 1
        return class_table



_clsreg = ClassRegistry()

def registered(cls):
    log.info("Registering class: %s" % cls.__name__)
    _clsreg.register( cls )
    return cls


def get_clsreg():
    return _clsreg

def ClsReg():
    return _clsreg


#
# Base declarative enhancement
#


def _generic_query(cls, dbsess = None):
    if dbsess is None:
        dbsess = dbsession
        print('DEPRECATED: please provide instance of RhoSession')
    assert isinstance(dbsess, RhoSession), 'FATAL PROG ERR: need to pass instance of RhoSession'
    return dbsess.query(cls)

Base.query = classmethod(_generic_query)

def _generic_get(cls, dbid, dbsess = None):
    q = cls.query(dbsess)
    return q.get(int(dbid))

Base.get = classmethod(_generic_get)

def _generic_lowername(cls):
    return cls.__name__.lower()

Base.lowername = classmethod(_generic_lowername)

def _generic_delete(cls, dbid, dbsess):
    q = cls.query(dbsess)
    return q.filter(cls.id == int(dbid)).delete()

Base.delete = classmethod(_generic_delete)



#
# SysReg - system registry
#

@registered
class SysReg(Base):

    __tablename__ = 'sysregs'
    id = Column(types.Integer, Sequence('sysreg_seqid', optional=True),
            primary_key=True)
    key = Column(types.String(64), nullable=False, unique=True)
    bindata = Column(types.LargeBinary, nullable=False)
    mimetype = Column(types.String(32), nullable=False)

    @staticmethod
    def getbykey(keyname, exception=True):
        if exception:
            return dbsession.query(SysReg).filter_by( key = keyname ).one()

        try:
            return dbsession.query(SysReg).filter_by( key = keyname ).one()
        except NoResultFound:
            return None

    @staticmethod
    def setdata(keyname, mimetype, value):
        if mimetype == 'text/json':
            bindata = json.dumps( value ).encode('UTF-8')
        elif mimetype == 'application/python-pickle':
            bindata = pickle.dumps( value )
        elif mimetype == 'application/octet-stream':
            bindata = value
        else:
            raise RuntimeError( 'unknown mimetype' )
        dbsession.add( SysReg( key=keyname, bindata=bindata, mimetype=mimetype ) )


    @staticmethod
    def getdata(keyname):
        ob = SysReg.getbykey(keyname)
        if ob.mimetype == 'text/json':
            return json.loads( ob.bindata.decode('UTF-8') )
        elif ob.mimetype == 'application/python-pickle':
            return pickle.loads( ob.bindata )
        elif ob.mimetype == 'application/octet-stream':
            return ob.bindata
        raise RuntimeError( 'unknown mimetype' )

# SysLog - system log

@registered
class SysLog(Base):

    __tablename__ = 'syslogs'
    id = Column(types.Integer, Sequence('syslog_seqid', optional=True),
            primary_key=True)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())
    level = Column(types.SmallInteger)
    msg = Column(types.String)


# DataLog - data log

@registered
class DataLog(Base):

    # this object should not be logged
    __typeid__ = -1

    __tablename__ = 'datalogs'
    id = Column(types.Integer, Sequence('datalog_seqid', optional=True),
            primary_key=True)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())
    class_id = Column(types.SmallInteger, nullable=False)
    object_id = Column(types.Integer, nullable=False)
    action_id = Column(types.SmallInteger, nullable=False)
    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=True,
                    default=get_userid, onupdate=get_userid)

    user = relationship('User', uselist=False)

    def action(self):
        return DataLogger._actions[self.action_id]

    def classname(self):
        return ClsReg().get_class( self.class_id ).__name__



class DataLogger(object):
    """ DataLogger needs to use connection or sql-level insert,
        conn = dbsession.connection()
        or
        dbsession.execute()
    """

    _actions = { 1: 'INSERT', 2: 'UPDATE', 3: 'DELETE' }

    def action_insert(self, instance):
        typeid, objid = instance.__class__.__typeid__, instance.id
        #entry = DataLog( class_id=typeid, object_id=objid, action_id=1 )
        #dbsession.add(entry)
        dbsession.execute( DataLog.__table__.insert().values(
                class_id = typeid, object_id = objid, action_id = 1, user_id = get_userid() ))

    def action_update(self, instance):
        typeid, objid = instance.__class__.__typeid__, instance.id
        #dbsession.add( DataLog( class_id=typeid, object_id=objid, action_id=2 ) )
        dbsession.execute( DataLog.__table__.insert().values(
                class_id = typeid, object_id = objid, action_id = 2, user_id = get_userid() ))


    def action_delete(self, instance):
        typeid, objid = instance.__class__.__typeid__, instance.id
        #dbsession.add( DataLog( class_id=typeid, object_id=objid, action_id=3 ) )
        dbsession.execute( DataLog.__table__.insert().values(
                class_id = typeid, object_id = objid, action_id = 3, user_id = get_userid() ))



class idcache_XXX(object):

    instances = {}

    def __init__(self):
        self._keys = {}
        self._ids = {}
        self.add_self(self)

    def get_key(self, id):
        return self._keys.get(id, None)

    def get_id(self, key):
        return self._ids.get(key, None)

    def set_key(self, key, id):
        self._ids[key] = id
        self._keys[id] = key

    def clear(self):
        self._keys = {}
        self._ids = {}

    def __del__(self):
        self.remove_self(self)

    @classmethod
    def add_self(cls, instance):
        cls.instances[instance] = instance

    @classmethod
    def remove_self(cls, instance):
        del cls.instances[instance]

    @classmethod
    def clear_all(cls):
        for instance in cls.instances.values():
            instance.clear()


def clear_caches_XXX(success):
    log.debug('Attempting to clear id caches')
    if not success:
        log.info('Clearing id caches')
        idcache.clear_all()

#current_t = transaction.get()
#current_t.addAfterCommitHook(clear_caches)


class BaseMixIn(object):
    """ BaseMixIn

        This is base class for all object that needs id, lastuser_id and
        stamp attribute.
    """

    @declared_attr
    def id(cls):
        return Column(  types.Integer,
                        Sequence('%s_seqid' % cls.__name__.lower(), optional=True),
                        primary_key=True )

    @declared_attr
    def lastuser_id(cls):
        return Column(  types.Integer,
                        ForeignKey('users.id'),
                        default = get_userid,
                        onupdate = get_userid,
                        nullable = True )

    @declared_attr
    def lastuser(cls):
        return relationship('User', uselist=False, foreign_keys=[cls.lastuser_id])

    @declared_attr
    def stamp(cls):
        return Column(types.TIMESTAMP, nullable=False, default=current_timestamp(),
            onupdate = now())
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


    @classmethod
    def bulk_load(cls, a_list, dbh):
        """ bulk load from a list of dictionary object """
        objs = [ cls.from_dict(d, dbh) for d in a_list ]
        dbh.session.flush(objs)


    @classmethod
    def from_dict(cls, a_dict, dbh):
        """ load and add from a dict """
        obj = cls()
        obj.update(a_dict)
        dbh.session().add(obj)
        return obj


    def as_dict(self):
        return dict(
            lastuser = self.lastuser.login,
            stamp = self.stamp,
        )
