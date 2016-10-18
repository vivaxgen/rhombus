
import sys

from rhombus.lib.utils import cerr, cout
from rhombus.models import (core, meta, ek, user, actionlog, filemgr)
from sqlalchemy import engine_from_config

cinfo = print


class DBHandler(object):

    # put the objectclass that we need to directly access here


    EK = ek.EK
    Group = user.Group
    User = user.User
    UserClass = user.UserClass


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
            setup( self )
            cerr('[rhombus] Database has been initialized.')


    def get_userclass(self, userclass=None):

        if userclass is None:
            return self.UserClass.query(self.session()).all()

        if type(userclass) == list:
            return [ self.get_userclass(x) for x in userclass ]

        if type(userclass) == int:
            return self.UserClass.get(userclass, self.session())
        else:
            return self.UserClass.search(userclass, self.session())

        raise RuntimeError('ERR: unknown data type for getting UserClass!')


    def get_user(self, user=None):

        if user is None:
            return self.User.query(self.session()).all()

        if type(user) == list:
            return [ self.get_user(u) for u in user ]

        if type(user) == int:
            return self.User.get(user, self.session())

        return self.User.search(user, session=self.session())


    def get_group(self, group=None, user_id=None):

        if group is None:
            if user_id is None:
                return self.get_groups()
            else:
                # only return groups where the user is a member
                raise NotImplementedError()

        if type(group) == list:
            return [ self.get_group(g) for g in group ]

        if type(group) == int:
            return self.Group.get(group, self.session())

        return self.Group.search(group, self.session())


    def get_groups(self):
        """ return all non-system groups """

        q = user.Group.query(self.session())
        q = q.filter( ~user.Group.name.startswith('\_', escape='\\') )
        return q.all()


    def get_user_by_id(self, id):
        return self.User.get(id, self.session())


    def get_user_by_email(self, email):
        q = self.User.query(self.session()).filter( self.User.email.ilike(email) )
        return q.one()


    def get_group_by_id(self, id):
        return self.Group.get(id, self.session())


    ## EnumeratedKey methods

    def add_ekey(self, ekey, group=None):
        group_ek = None
        if group:
            group_ek = ek.EK.search(group, dbsession=self.session())


        if not group_ek and not ekey.startswith('@'):
            raise RuntimeError('ekey must be under a group, or starts with @')

        new_ekey = ek.EK( ekey, '-', parent=group_ek)
        self.session().add(new_ekey)
        return new_ekey


    def list_ekeys(self, group=None):
        if group:
            return ek.EK.getmembers(group, self.session())
        else:
            return ek.EK.query(self.session()).filter( ek.EK.key.startswith('@') ).all()


    def get_ekey(self, ekey):
        return self.EK.search(ekey, dbsession = self.session())


