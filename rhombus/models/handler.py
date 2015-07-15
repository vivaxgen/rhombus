
import sys

from rhombus.lib.utils import cerr, cout
from rhombus.models import (core, meta, ek, user, actionlog, filemgr)
from sqlalchemy import engine_from_config

cinfo = print


class DBHandler(object):

    # put the objectclass that we need to directly access here


    EK = ek.EK


    def __init__(self, settings, tag='sqlalchemy.', initial = False):
        """ use settings from configfile, prepare self.engine & self.session """
        cinfo("Connecting to database..")

        self.engine = engine_from_config(settings, tag)

        use_logger = False
        if 'rhombus.data_logger' in settings:
            use_logger = settings['rhombus.data_logger']

        if not initial and use_logger == 'true':
            cinfo('data logger is being used!')
            data_logger = DataLogger()
            set_datalogger( data_logger )

            get_clsreg().sync()

        self.settings = settings
        self.session = meta.get_dbsession()
        self.session.configure(bind = self.engine )



    def initdb(self):
        """ prepare the database for the first time by initializing it with
            necessary, basic, default data set """
        
        # WARN! if possible, use alembic to create tables
        core.Base.metadata.create_all(self.engine)
        
        from rhombus.models.setup import setup
        setup( self.session )
        cinfo('[rhombus] Database has been initialized')


    def get_userclass(self, userclass):

        uc = user.UserClass.search(userclass, self.session)
        return uc


    def get_groups(self):

        q = user.Group.query(self.session)
        q = q.filter( ~user.Group.name.startswith('\_', escape='\\') )
        return q.all()

    def get_group_by_id(self, id):
        return user.Group.get(id)


