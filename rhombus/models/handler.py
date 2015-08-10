
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



    def initdb(self, create_table=True, init_data=True):
        """ prepare the database for the first time by initializing it with
            necessary, basic, default data set """
        
        # WARN! if possible, use alembic to create tables
        if create_table:
            core.Base.metadata.create_all(self.engine)
            cerr('[rhombus] Database tables created.')

        if init_data:
            from rhombus.models.setup import setup
            setup( self.session )
            cerr('[rhombus] Database has been initialized.')


    def get_userclass(self, userclass):

        uc = user.UserClass.search(userclass, self.session)
        return uc


    def get_groups(self):

        q = user.Group.query(self.session)
        q = q.filter( ~user.Group.name.startswith('\_', escape='\\') )
        return q.all()

    def get_group_by_id(self, id):
        return user.Group.get(id)


    def add_ekey(self, ekey, group=None):
        group_ek = None
        if group:
            group_ek = ek.EK.search(group, dbsession=self.session)


        if not group_ek and not ekey.startswith('@'):
            raise RuntimeError('ekey must be under a group, or starts with @')

        new_ekey = ek.EK( ekey, '-', parent=group_ek)
        self.session.add(new_ekey)
        return new_ekey


    def list_ekeys(self, group=None):
        if group:
            return ek.EK.getmembers(group, self.session())
        else:
            return ek.EK.query(self.session()).filter( ek.EK.key.startswith('@') ).all()


