
import sys

from rhombus.lib.utils import cerr, cout
from rhombus.models import (core, meta, ek, user, actionlog, filemgr)
from sqlalchemy import engine_from_config, event, or_, and_
from sqlalchemy.orm import exc

cinfo = print


#
# query constructor
#

class QueryConstructor(object):

    # field specs contains field_tag: column_class
    field_specs = {
        'userclass_id': user.UserClass.id,
        'user_id': user.User.id,
        'group_id': user.Group.id,
    }

    def __init__(self):
        pass

    def construct_query_from_list(self, a_list):
        exprs = []
        classes = []
        for spec in a_list:
            spec_exprs, spec_classes = self.construct_query_from_dict(spec)
            exprs.append(spec_exprs)
            classes.extend(spec_classes)

        classes = set(classes)
        return or_(* exprs), classes

    def construct_query_from_dict(self, a_dict):

        exprs = []
        classes = []

        for k, val in a_dict.items():
            f = self.field_specs[k]
            if f.class_ not in classes:
                classes.append(f.class_)
            if isinstance(val, list):
                exprs.append(f.in_(val))
            elif isinstance(val, tuple):
                exprs.append(f.in_(val))
            elif '%' in val:
                exprs.append(f.ilike(val))
            else:
                exprs.append(f == val)

        return and_(*exprs), classes

    field_specs = {
        'userclass_id': user.UserClass.id,
        'userclass_domain': user.UserClass.domain,

        'user_id': user.User.id,
        'user_login': user.User.login,
    }


class DBHandler(object):

    # put the objectclass that we need to directly access here

    EK = ek.EK
    Group = user.Group
    User = user.User
    UserClass = user.UserClass
    UserGroup = user.UserGroup

    query_constructor_class = QueryConstructor

    def __init__(self, settings, tag='sqlalchemy.', initial=False):
        """ use settings from configfile, prepare self.engine & self.session """
        cinfo("Connecting to database..")

        self.engine = engine_from_config(settings, tag)

        # check if SQLite, then set pragma
        if self.engine.name.startswith('sqlite'):
            event.listen(self.engine, 'connect', meta.set_sqlite_pragma)

        use_logger = False
        if 'rhombus.data_logger' in settings:
            use_logger = settings['rhombus.data_logger']

        if not initial and use_logger == 'true':
            cinfo('data logger is being used!')
            data_logger = core.DataLogger()
            meta.set_datalogger(data_logger)

            core.get_clsreg().sync()

        self.settings = settings
        self.session = meta.get_dbsession()
        self.session.configure(bind=self.engine)
        self._query_constructor = None

    def initdb(self, create_table=True, init_data=True, rootpasswd=None):
        """ prepare the database for the first time by initializing it with
            necessary, basic, default data set """

        # WARN! if possible, use alembic to create tables
        if create_table:
            core.Base.metadata.create_all(self.engine)
            cerr('[rhombus] Database tables created.')

        if init_data:
            from rhombus.models.setup import setup
            setup(self, rootpasswd)
            cerr('[rhombus] Database has been initialized.')

    def get_userclass(self, userclass=None):

        if userclass is None:
            return self.UserClass.query(self.session()).all()

        if type(userclass) == list:
            return [self.get_userclass(x) for x in userclass]

        if type(userclass) == int:
            return self.UserClass.get(userclass, self.session())
        else:
            return self.UserClass.search(userclass, self.session())

        raise RuntimeError('ERR: unknown data type for getting UserClass!')

    def get_user(self, user=None):

        if user is None:
            return self.User.query(self.session()).all()

        if type(user) == list:
            return [self.get_user(u) for u in user]

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
            return [self.get_group(g) for g in group]

        if type(group) == int:
            return self.Group.get(group, self.session())

        return self.Group.search(group, self.session())

    def get_groups(self):
        """ return all non-system groups """

        q = user.Group.query(self.session())
        q = q.filter(~user.Group.name.startswith('\\_', escape='\\'))
        return q.all()

    def get_user_by_id(self, id):
        return self.User.get(id, self.session())

    def get_user_by_email(self, email):
        q = self.User.query(self.session()).filter(self.User.email.ilike(email))
        return q.all()

    def get_group_by_id(self, id):
        return self.Group.get(id, self.session())

    # EnumeratedKey methods

    def add_ekey(self, ekey, group=None):
        group_ek = None
        if group:
            group_ek = ek.EK.search(group, dbsession=self.session())

        if not group_ek and not ekey.startswith('@'):
            raise RuntimeError('ekey must be under a group, or starts with @')

        new_ekey = ek.EK(ekey, '-', parent=group_ek)
        self.session().add(new_ekey)
        return new_ekey

    def list_ekeys(self, group=None):
        if group:
            return ek.EK.getmembers(group, self.session())
        else:
            return ek.EK.query(self.session()).filter(ek.EK.key.startswith('@')).all()

    def get_ekey(self, ekey, group=None):
        return self.EK.search(ekey, group=group, dbsession=self.session())

    def get_ek_id(self, key, group=None):
        return self.EK._id(key, grp=group, dbsession=self.session())

    # Universal query system

    def get_query_constructor(self):
        if self._query_constructor is None:
            self._query_constructor = self.query_constructor_class()
        return self._query_constructor

    def construct_query(self, object, selector):
        """ return compound query constructed from list & dictionary

            return objects with samples_id in [0, 1, 2] OR collection_id in [ 5 ]
            [
                {'sample_id': [0, 1, 2]},
                {'collection_id': [5]}
            ]
            filter( or_( Sample.id.in_([0,1,2]), Collection.id.in_([5]) ) )

            return objects with category_id in [1,2] AND collection_id in [ 5 ]
            [
                {'category_id': [1, 2], 'collection_id': [5]}
            ]
            filter ( or_( and_(Category.id.in_([1,2]), Collection.id.in_([5])) ) )
        """

        q = self.session().query(object)

        selector = selector or []
        constructor = self.get_query_constructor()
        filter_expr, filter_classes = constructor.construct_query_from_list(selector)
        filter_classes = filter_classes - {object}

        for class_ in filter_classes:
            q = q.join(class_)

        q = q.filter(filter_expr)
        return q

    def fetch_query(self, query, fetch, raise_if_empty):
        """ prepare query results, either the query itself, the fetched objects
            or raised exception if necessary
        """
        if not fetch:
            return query

        res = query.all()
        if raise_if_empty and len(res) == 0:
            raise exc.NoResultFound()
        return res

# end of file
