
from rhombus.models import (core, meta, ek, user, actionlog, filemgr)
#from .core import *
#from .meta import *
#from .ek import *
#from .user import *
#from .actionlog import *
#from .filemgr import *
from sqlalchemy import engine_from_config

cinfo = print


def init_db(settings, create_table=False):
    """ call this function before doing any database operation

        This function sets up the database connection, optionally creates all SQL tables,
        and if needed, preparing data logger and synchronizing class registration with
        the database.

        This function _has_ to be called _after_ doing multiprocessing forking/init,
        and each process needs to call this function separately.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    use_logger = settings['rhombus.data_logger']

    dbsession = get_dbsession()
    dbsession.configure(bind=engine)
    base = get_base()
    base.metadata.bind = engine

    if create_table:
        base.metadata.create_all( engine )

    if use_logger == 'true':
        print('INFO: data logger is being used!')
        data_logger = DataLogger()
        set_datalogger( data_logger )
        
        get_clsreg().sync()

    return engine



