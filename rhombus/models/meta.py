__copyright__ = '''
meta.py - Rhombus SQLAlchemy metadata, mapper and session object

(c) 2011 - 2015 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

__revision__ = '20151008'

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, mapper, Session
from sqlalchemy.engine import Engine
from sqlalchemy import event, MetaData

from zope.sqlalchemy import ZopeTransactionExtension

__all__ = ['get_base', 'get_dbsession', 'set_datalogger']

class RhoSession(Session):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # EK idcache
        self._ek_keys = {}
        self._ek_ids = {}

        # current user information
        self.user = None
        self.global_user = None	# used for per-process user (eg. in scripts)

    def close(self):
        self.user = None
        super().close()

    ## EK helpers

    def get_key(self, id):
        return self._ek_keys.get(id, None)

    def get_id(self, key):
        return self._ek_ids.get(key, None)

    def set_key(self, key, id):
        self._ek_ids[key] = id
        self._ek_keys[id] = key

    def clear_keys(self):
        self._ek_keys.clear()
        self._ek_ids.clear()


@event.listens_for(RhoSession, 'after_transaction_end')
def clear_session_cache(session, tx):
    session.clear_keys()


@event.listens_for(mapper, 'before_update')
def update_lastuser(mapper, conn, instance):
    if hasattr(instance, '__before_update__'):
        instance.__before_update__()


def uq_convention(constraint, table):
    names = [ table.name]
    names += [ str(c).split('.')[-1] for c in constraint.columns ]
    return "_".join( names )

def ck_convention(constraint, table):
    # TODO: need more careful implementation here
    #print(dir(constraint))
    #print('table name:', table.name)
    return "CK"


convention = {
  "ix": 'ix_%(column_0_label)s',
  "uq_custom": uq_convention,
  #"uq": "uq_%(table_name)s_%(column_0_name)s",
  "uq": "uq_%(uq_custom)s",
  #"ck": "ck_%(table_name)s_%(constraint_name)s",
  "ck_custom": ck_convention,
  "ck": "ck_%(ck_custom)s",
  "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
  "pk": "pk_%(table_name)s"
}

_metadata = MetaData(naming_convention=convention)
_dbsession = scoped_session(sessionmaker(class_ = RhoSession,
                                        extension = ZopeTransactionExtension()))
_base = declarative_base(metadata=_metadata)

# this is necessary for SQLite to use FOREIGN KEY support (as well as ON DELETE CASCADE)
#@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    #raise RuntimeError(dir(connection_record))
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


# Rhombus data logger

_datalogger = None

def _check_target(target):
    try:
        if _datalogger is not None and target.__class__.__typeid__ != -1:
            return True
    except AttributeError:
        pass
    return False

def _after_insert_listener(mapper, connection, target):
    if _check_target(target):
        _datalogger.action_insert(target)

def _after_update_listener(mapper, connection, target):
    if _check_target(target):
        _datalogger.action_update(target)

def _after_delete_listener(mapper, connection, target):
    if _check_target(target):
        _datalogger.action_delete(target)


# public functions

def set_datalogger(logger):
    """ set the datalogger and register events to be listened """

    global _datalogger
    _datalogger = logger
    event.listen(mapper, 'after_insert', _after_insert_listener)
    event.listen(mapper, 'after_update', _after_update_listener)
    event.listen(mapper, 'after_delete', _after_delete_listener)


def get_datalogger():
    return _datalogger


def get_base():
    return _base

def get_dbsession():
    return _dbsession
