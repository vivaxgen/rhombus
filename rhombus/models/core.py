__copyright__ = '''
core.py - Rhombus SQLAlchemy core objects

(c) 2011 - 2021 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

import logging

from sqlalchemy import and_, or_, schema, types, MetaData, Sequence, Column, ForeignKey, UniqueConstraint, Table, Identity
from sqlalchemy.orm import relationship, backref, dynamic_loader, deferred, column_property
from sqlalchemy.orm.collections import column_mapped_collection, attribute_mapped_collection
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql.functions import current_timestamp, now

from rhombus.lib.utils import get_userid, get_groupid, set_func_userid

import json
import transaction
import pickle
import threading
import functools

from .meta import get_base, get_dbsession, get_datalogger, RhoSession
from .auxtypes import UUID, YAMLCol, JSONCol
from .stampmixin import StampMixIn
from .autoupdatemixin import AutoUpdateMixIn

log = logging.getLogger(__name__)
__version__ = '20210702'


# global variables

Base = get_base()
dbsession = get_dbsession()
metadata = Base.metadata


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
            if cls.__typeid__ == -1:
                return
        self._classes[cls.lowername()] = cls
        cls.__typeid__ = None

    def sync(self):

        assert get_datalogger(), "ERROR: ClassRegistry.sync() should not be called!"

        log.info("Synchronizing class table registry...")

        try:
            log.info('Reading class registry...')
            class_table = SysReg.getdata('__class_table__')
            if class_table is None:
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

    def update_table(self, class_table={}, nextid=1):

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
    _clsreg.register(cls)
    return cls


def get_clsreg():
    return _clsreg


def ClsReg():
    return _clsreg


#
# Base declarative enhancement
#


def _generic_query(cls, dbsess=None):
    if dbsess is None:
        dbsess = dbsession
        print('DEPRECATED: please provide instance of RhoSession')
    assert isinstance(dbsess, RhoSession), 'FATAL PROG ERR: need to pass instance of RhoSession'
    return dbsess.query(cls)


Base.query = classmethod(_generic_query)


def _generic_get(cls, dbid, dbsess=None):
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
    id = Column(types.Integer, Identity(), primary_key=True)
    key = Column(types.String(64), nullable=False, unique=True)
    bindata = Column(types.LargeBinary, nullable=False)
    mimetype = Column(types.String(32), nullable=False)

    @staticmethod
    def getbykey(keyname, exception=True):
        if exception:
            return dbsession.query(SysReg).filter_by(key=keyname).one()

        try:
            return dbsession.query(SysReg).filter_by(key=keyname).one()
        except NoResultFound:
            return None

    @staticmethod
    def setdata(keyname, mimetype, value):
        if mimetype == 'text/json':
            bindata = json.dumps(value).encode('UTF-8')
        elif mimetype == 'application/python-pickle':
            bindata = pickle.dumps(value)
        elif mimetype == 'application/octet-stream':
            bindata = value
        else:
            raise RuntimeError('unknown mimetype')
        dbsession.add(SysReg(key=keyname, bindata=bindata, mimetype=mimetype))


    @staticmethod
    def getdata(keyname):
        ob = SysReg.getbykey(keyname)
        if ob.mimetype == 'text/json':
            return json.loads(ob.bindata.decode('UTF-8'))
        elif ob.mimetype == 'application/python-pickle':
            return pickle.loads(ob.bindata)
        elif ob.mimetype == 'application/octet-stream':
            return ob.bindata
        raise RuntimeError('unknown mimetype')

# SysLog - system log


@registered
class SysLog(Base):

    __tablename__ = 'syslogs'
    id = Column(types.Integer, Identity(), primary_key=True)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())
    level = Column(types.SmallInteger)
    msg = Column(types.String(256))


# DataLog - data log

@registered
class DataLog(Base):

    # this object should not be logged
    __typeid__ = -1

    __tablename__ = 'datalogs'
    id = Column(types.Integer, Identity(), primary_key=True)
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
        return ClsReg().get_class(self.class_id).__name__


class DataLogger(object):
    """ DataLogger needs to use connection or sql-level insert,
        conn = dbsession.connection()
        or
        dbsession.execute()
    """

    _actions = {1: 'INSERT', 2: 'UPDATE', 3: 'DELETE'}

    def action_insert(self, instance):
        typeid, objid = instance.__class__.__typeid__, instance.id
        dbsession.execute(DataLog.__table__.insert().values(
                          class_id=typeid, object_id=objid, action_id=1, user_id=get_userid()))

    def action_update(self, instance):
        typeid, objid = instance.__class__.__typeid__, instance.id
        dbsession.execute(DataLog.__table__.insert().values(
                          class_id=typeid, object_id=objid, action_id=2, user_id=get_userid()))

    def action_delete(self, instance):
        typeid, objid = instance.__class__.__typeid__, instance.id
        dbsession.execute(DataLog.__table__.insert().values(
                          class_id=typeid, object_id=objid, action_id=3, user_id=get_userid()))


class BaseMixIn(StampMixIn, AutoUpdateMixIn):
    """ BaseMixIn combined StampMixIn with AutoUpdate MixIn)
    """

# EOF
