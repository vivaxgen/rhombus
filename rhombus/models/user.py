from .core import *
from .ek import *

from rhombus.lib.auth import authfunc
from rhombus.lib.roles import SYSADM, DATAADM
from passlib.hash import sha256_crypt as pwcrypt

import yaml
from pprint import pprint


@registered
class UserClass(Base):

    __tablename__ = 'userclasses'
    id = Column(types.Integer, Sequence('userclass_seq_id', optional=True),
        primary_key=True)
    domain = Column(types.String(16), nullable=False, unique=True)
    desc = Column(types.String(64), nullable=False)
    referer = Column(types.String(128), nullable=False, server_default='')
    autoadd = Column(types.Boolean, nullable=False, default=False)
    credscheme = Column(YAMLCol(256), nullable=False)  # YAML type data
    flags = Column(types.Integer, nullable=False, server_default='0')


    def __repr__(self):
        return "%s" % self.domain


    def update(self, d):

        if isinstance(d, dict):
            self.domain = d['domain']
            self.desc = d['desc']
            self.credscheme = d['credscheme']
            if 'referer' in d:
                self.referer = d['referer']
            if 'autoadd' in d:
                self.autoadd = d['autoadd']
            if 'credscheme' in d:
                self.credscheme = d['credscheme']

        else:
            raise RuntimeError('updating can only be performed using dict ')


    @staticmethod
    def search(domain, session):
        q = session.query(UserClass).filter(UserClass.domain == domain).all()
        if q: return q[0]
        return None


    @staticmethod
    def allclasses():
        return [ (x.id, x.domain) for x in UserClass.query().order_by( UserClass.domain ).all() ]

    def auth_user(self, username, passwd):
        """ return UserInstance or None """
        if not (username and passwd):
            return None

        user = User.search( username, self )
        if not user and not self.autoadd:
            return None

        # password checking performed here
        if (not user and self.autoadd) or (user and user.credential == '{X}'):
            # credential will be checked by the underlying scheme
            ok = authfunc[self.credscheme['sys']](username, passwd, self.credscheme)
            if ok:
                if not user:
                    user = User( login = username, credential = '{X}' )
                    self.users.add( user )
                    dbsession.commit()
                return user.user_instance()
        elif user and user.verify_credential(passwd):
            return user.user_instance()

        return None

    def as_dict(self):
        return dict(id=self.id, domain=self.domain, desc = self.desc,
                    referer = self.referer, autoadd = self.autoadd,
                    credscheme = self.credscheme,
                    users = [ u.as_dict() for u in self.users ] )


    @staticmethod
    def bulk_insert(userclass, dbsession):
        """ inserting userclass and its users with folowing data structure:
            [
                ( domain, desc, referer, credscheme,
                    [   ( login, lastname, firstname, email, pri_group, cred, [ groups ] ),
                        ... ] ),
                ...
            ]
        """
        print(len(userclass))
        pprint(userclass)
        domain, desc, referer, credscheme, userlist = tuple(userclass)
        uc = UserClass( domain=domain, desc=desc, referer=referer, credscheme=credscheme )
        dbsession.add(uc)
        for user in userlist:
            login, lastname, firstname, email, p_grp = user[:5]
            if len(user) >= 7:
                grps = user[6]
            else:
                grps = []
            u = uc.add_user( login, lastname, firstname, email, p_grp, grps )
            if len(user) >= 6:
                u.set_credential( user[5] )


    def add_user(self, login, lastname, firstname, email, primarygroup, groups=[]):
        """ add a new user """

        session = object_session(self)
        pri_grp = Group.search(primarygroup, session)
        user_instance = User(login=login, userclass=self,
                            lastname=lastname, firstname=firstname, email=email,
                            primarygroup = pri_grp, credential='{X}')
        # set as member for primary group too
        pri_grp.users.append(user_instance)

        if groups:
            for grp in groups:
                g = Group.search(grp, session)
                g.users.append(user_instance)
        return user_instance


    def search_user(self, login):
        return User.search(login, self)


    def get_user(self, login):
        return User.search(login, self)


    @classmethod
    def from_dict(cls, d):
        uc = UserClass()
        uc.update(d)

        from rhombus.lib.utils import get_dbhandler

        get_dbhandler().session().add(uc)

        if 'users' in d:
            for user_dict in d['users']:
                user = User.from_dict(user_dict, userclass = uc)

        return uc


    @staticmethod
    def dump(out, userclasses):
        """ dump data to YAML-formatted file """
        yaml.safe_dump_all( ( x.as_dict() for x in userclasses ), out, default_flow_style=False )


@registered
class UserData(Base):

    __tablename__ = 'userdatas'
    id = Column(types.Integer, Sequence('userdata_seq_id', optional=True), primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False, index=True)
    key_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False, index=True)
    bindata = Column(types.LargeBinary, nullable=False)
    mimetype = Column(types.String(32), nullable=False)


@registered
class User(Base):

    __tablename__ = 'users'
    id = Column(types.Integer, Sequence('user_seq_id', optional=True),
        primary_key=True)
    login = Column(types.String(32), unique=True, nullable=False)
    credential = Column(types.String(128), nullable=False)
    lastlogin = Column(types.TIMESTAMP)
    userclass_id = Column(types.Integer, ForeignKey('userclasses.id'), nullable=False,
                    index=True)
    lastname = Column(types.String(32), index=True, nullable=False)
    firstname = Column(types.String(32), nullable=False, server_default='')
    email = Column(types.String(32), index=True, nullable=False)
    institution = Column(types.String(64), nullable=False, server_default='')
    address = Column(types.String(128), nullable=False, server_default='')
    contact = Column(types.String(64), nullable=False, server_default='')
    status = Column(types.String(1), nullable=False, server_default='A')
    flags = Column(types.Integer, nullable=False, server_default='0')

    primarygroup_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False, index=True)

    yaml = deferred(Column(YAMLCol))
    __table_args__ = ( UniqueConstraint('login', 'userclass_id'), {} )

    userclass = relationship(UserClass, uselist=False, backref=backref('users', lazy='dynamic'))
    primarygroup = relationship('Group', uselist=False, backref=backref('primaryusers'))
    userdata = relationship(UserData,
                    collection_class = column_mapped_collection(UserData.key_id),
                    cascade='all,delete,delete-orphan')
    groups = association_proxy('usergroups', 'group')

    def __repr__(self):
        return "%s/%s" % (self.login, str(self.userclass).lower())

    def get_login(self):
        return "%s/%s" % (self.login, self.userclass.domain)

    def update(self, u):
        if isinstance(u, dict):
            if 'lastname' in u:
                self.lastname = u['lastname']
            if 'firstname' in u:
                self.firstname = u['firstname']
            if 'email' in u:
                self.email = u['email']
            if 'institution' in u:
                self.institution = u['institution']
            if 'address' in u:
                self.address = u['address']
            if 'contact' in u:
                self.contact = u['contact']
            if 'primarygroup_id' in u:
                self.set_primarygroup(u['primarygroup_id'])

        else:
            self.lastname = u.lastname
            self.firstname = u.firstname
            self.email = u.email
            self.institution = u.institution
            self.address = u.address
            self.contact = u.contact
            if u.primarygroup_id:
                self.set_primarygroup(u.primarygroup_id)


    def fullname(self):
        return '%s, %s' % (self.lastname, self.firstname)


    def set_primarygroup(self, grp):
        if type(grp) == int:
            primarygroup_id = grp
        else:
            primarygroup_id = grp.id

        session = object_session(self)

        if self.primarygroup_id:
            if self.primarygroup_id == primarygroup_id:
                return

            # remove from previous group
            UserGroup.delete(session, self.id, self.primarygroup_id)

        self.primarygroup_id = primarygroup_id
        UserGroup.add(session, self.id, primarygroup_id)


    @staticmethod
    def search(login, userclass=None, session=None):
        if userclass:
            dbsession = object_session(userclass)
        elif session:
            dbsession = session
        else:
            raise RuntimeError('ERR: need to provide either userclass or dbsession')
        if '/' in login:
            login, domain = login.split('/', 1)
            userclass = UserClass.search(domain, dbsession)
        q = dbsession.query(User).filter(and_(User.login == login, User.userclass == userclass))
        r = q.all()
        if r: return r[0]
        return None

    def set_pref(self, key, data):
        g_jsoncache.set_data(self, key, data)

    def get_pref(self, key, default):
        return g_jsoncache.get_data(self, key, default)

    def raw_pref(self):
        return g_jsoncache.raw_data(self)

    def save_pref(self):
        g_jsoncache.save_data(self)

    def groupids(self):
        dbsession = object_session(self)
        return [ x.group_id for x in UserGroup.query(dbsession).filter( UserGroup.user_id == self.id ).all() ]

    def group_role_ids(self):
        dbsession = object_session(self)
        grp_ids = [ x.group_id for x in UserGroup.query(dbsession).filter( UserGroup.user_id == self.id ).all() ]
        res = dbsession.execute( group_role_table.select( group_role_table.c.group_id.in_( grp_ids ) ).with_only_columns([group_role_table.c.role_id]).distinct())
        role_ids = [ item for sublist in res.fetchall() for item in sublist ]
        return ( grp_ids, role_ids )

    def group_users(self):
        dbsession = object_session(self)
        if self.has_roles(SYSADM):
            return User.query(dbsession).all()
        group_ids = self.groupids()
        user_ids = [ x.user_id for x in UserGroup.query(dbsession).filter( UserGroup.group_id.in_( group_ids ))]
        return [ User.get(u, dbsession) for u in set(user_ids) ]

    def has_roles(self, *roles):
        grp_ids, role_ids = self.group_role_ids()
        for role in roles:
            role_id = EK._id(role)
            if role_id in role_ids:
                return True
        return False

    def user_instance(self):
        group_ids, role_ids = self.group_role_ids()
        return UserInstance( self.login, self.id, self.primarygroup_id,
                self.userclass.domain, group_ids, role_ids, dbsession = object_session(self) )

    def render(self):
        return "%s | %s" % (str(self), self.fullname())

    def as_dict(self):
        return dict( id = self.id, login = self.login, credential = self.credential,
                lastlogin = self.lastlogin, userclass = self.userclass.domain,
                lastname = self.lastname, firstname = self.firstname,
                institution = self.institution, address = self.address, contact = self.contact,
                status = self.status, primarygroup = self.primarygroup.name,
                groups = [ [ug.group.name, ug.role] for ug in self.usergroups ] )

    def set_credential(self, passwd):
        if passwd == '{X}':
            self.credential = passwd
        else:
            self.credential = pwcrypt.encrypt(passwd)

    def verify_credential(self, passwd):
        if self.credential == '{X}':
            raise RuntimeError('this password use external system')
        return pwcrypt.verify(passwd, self.credential)


    @staticmethod
    def dump(out, query = None):
        import yaml
        if not query:
            query = User.query()
        yaml.dump_all( (x.as_dict() for x in query), out, default_flow_style=False )


def _create_ug_by_user(user):
    return UserGroup(user=user)

group_role_table = Table('groups_roles', metadata,
    Column('id', types.Integer, Sequence('group_role_seqid', optional=True),
        primary_key=True),
    Column('group_id', types.Integer, ForeignKey('groups.id'), nullable=False),
    Column('role_id', types.Integer, ForeignKey('eks.id'), nullable=False),
    UniqueConstraint( 'group_id', 'role_id' )
)


@registered
class Group(Base):

    __tablename__ = 'groups'
    id = Column(types.Integer, Sequence('group_seq_id', optional=True), primary_key=True)
    name = Column(types.String(32), nullable=False, unique=True)
    desc = Column(types.String(128), nullable=False, server_default='')
    scheme = Column(YAMLCol(256), nullable=False, server_default='')
    flags= Column(types.Integer, nullable=False, server_default='0', default=0)

    #users = relationship(User, secondary=user_group_table, backref=backref('groups'))
    users = association_proxy('usergroups', 'user', creator=_create_ug_by_user)
    roles = relationship(EK, secondary=group_role_table, order_by = EK.key)

    # flags
    f_composite_group = 1 << 0

    def __repr__(self):
        return "<Group: %s>" % self.name

    def has_member(self, user):
        if type(user) == int:
            if (self.flags & self.f_composite_group):
                # join UserGroup and AssociatedGroup
                user_ids = [ x[0] for x in list(AssociatedGroup.get_usergroup_info_query(self, 'C'))
                ]
            else:
                user_ids = [ x[0] for x in
                                object_session(self).query(UserGroup.user_id).\
                                filter( UserGroup.group_id == self.id)
                ]
                #user_ids = [ x.user_id for x in UserGroup.query().filter( UserGroup.group_id == self.id ).all() ]
            return user in user_ids
        elif type(user) == UserInstance:
            return user.in_group(self)
        else:
            return user in self.users

    def is_admin(self, user):
        if not type(user) == int:
            user_id = user.id
        else:
            user_id = user

        if (self.flags & self.f_composite_group):
            uginfo = AssociatedGroup.get_usergroup_info_query(self, 'C').filter( UserGroup.user_id == user_id).one()
            if ug and uginfo[1] == 'A':
                return True
            return False

        ug = UserGroup.query(object_session(self)).filter( UserGroup.group_id == self.id,
                    UserGroup.user_id == user_id ).one()
        if ug and ug.role == 'A':
            return True
        return False

    def check_flags(self, flag):
        return self.flags & flag

    def set_flags(self, flag, val):
        self.flags = (self.flags | flag) if val == True else (self.flags & ~flag)

    def render(self):
        if self.desc:
            return "%s | %s" % (self.name, self.desc)
        return self.name

    @staticmethod
    def search(grpname, dbsession):
        if type(grpname) == int:
            return Group.get(grpname, dbsession)
        q = Group.query(dbsession).filter(Group.name == grpname).all()
        if q: return q[0]
        return None

    @staticmethod
    def _id(grpname, dbsession):
        assert dbsession
        grp = Group.search(grpname, dbsession = dbsession)
        if grp:
            return grp.id
        return 0

    @staticmethod
    def bulk_insert(grplist, dbsession):
        """ grplist = [ (grpname, desc, role_list) ] """
        print(grplist)
        for grpitem in grplist:
            if len(grpitem) == 3:
                grpname, desc, roles = grpitem[0], grpitem[1], grpitem[2]
            else:
                grpname, desc, roles = grpitem[0], grpitem[0], grpitem[1]
            grp = Group(name = grpname, desc=desc)
            dbsession.add(grp)
            for role in roles:
                grp.roles.append( EK.search(role, dbsession = dbsession) )

    def update(self, obj):
        if type(obj) == dict:
            self.name = obj['name']
            self.desc = obj['desc']
            self.scheme = obj['scheme']

            # flags
            if 'flags-on' in obj:
                self.flags |= obj['flags-on']
            if 'flags-off' in obj:
                self.flags &= ~ obj['flags-off']

            if 'composite_ids' in obj:
                if not self.id:
                    # this is new object, so we can just attach using SqlAlchemy relationship mechanism
                    session = get_dbhandler().session()
                    with session.no_autoflush:
                        for ag_id in obj['composite_ids']:
                            AssociatedGroup.add(self.id, ag_id, 'C', session)

                    #raise RuntimeError('FATAL ERR: node does not have id while performing tagging')
                else:
                    AssociatedGroup.sync( self.id, obj['composite_ids'], session = object_session(self) )
            return

        self.name = obj.name
        self.desc = obj.desc
        self.scheme = obj.scheme

    def as_dict(self):
        return dict( name=self.name, desc=self.desc, scheme=self.scheme,
                users = [ (ug.user.login, ug.role) for ug in self.usergroups ] )

    @staticmethod
    def dump(out, query=None):
        if query is None:
            query = Group.query()
        yaml.safe_dump_all( (x.as_dict() for x in query), out, default_flow_style=False)


@registered
class UserGroup(Base):

    __tablename__ = 'users_groups'
    id = Column(types.Integer, Sequence('user_group_seq_id', optional=True),
            primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    role = Column(types.String(1), nullable=False, server_default='M')

    __table_args__ = ( UniqueConstraint('user_id', 'group_id'), {} )

    user = relationship(User, uselist=False,
        backref=backref('usergroups', cascade='all,delete,delete-orphan'))
    group = relationship(Group, uselist=False, backref='usergroups')

    def __init__(self, user=None, group=None, role = None):
        self.user = user
        self.group = group
        self.role = role

    @staticmethod
    def add(session, user, group, role='M'):
        if type(user) == int:
            user = User.get(user, session)
        if type(group) == int:
            group = Group.get(group, session)
        ug = UserGroup(user, group, role)
        session.add( ug )


    @staticmethod
    def delete(session, user_id, group_id):
        ug = UserGroup.query(session).filter(UserGroup.user_id == user_id,
                    UserGroup.group_id == group_id).one()
        session.delete( ug )


@registered
class AssociatedGroup(Base):

    __tablename__ = 'associated_groups'
    id = Column(types.Integer, Sequence('associated_group_seq_id', optional=True),
            primary_key=True)
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    assoc_group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    role = Column(types.String(1), nullable=False, server_default='R')

    group = relationship(Group, uselist=False, foreign_keys=[ group_id ],
                backref=backref('associated_groups', cascade='all,delete,delete-orphan'))
    associated_group = relationship(Group, uselist=False, foreign_keys=[ assoc_group_id ])

    __table_args__ = (UniqueConstraint('group_id', 'assoc_group_id'), {})


    @classmethod
    def get_usergroup_info_query(cls, group, role=None):
        """ return tuples of (user_id, group_id, role) for those associated with the group
        """
        q = object_session(group).query( UserGroup.user_id, UserGroup.role, UserGroup.group_id, cls.role ).\
                filter( UserGroup.group_id == cls.assoc_group_id, cls.group_id == group.id)
        if role:
            q = q.filter( cls.role == role )
        return q

    @classmethod
    def sync(cls, group_id, group_ids, role='C', session = None):
        # synchronize node_id and tag_ids

        # check sanity
        assert type(group_id) == int
        for id in group_ids:
            if type(id) != int:
                raise RuntimeError('FATAL ERR: tag_ids must contain ony integers')

        if not session:
            session = get_dbhandler().session()

        ags = cls.query(session).filter(cls.group_id == group_id)
        in_sync = []
        for ag in ags:
            if ag.assoc_group_id in group_ids:
                in_sync.append( ag.assoc_group_id )
            else:
                # remove this tag
                session.delete(ag)

        print(in_sync)
        for grp_id in group_ids:
            if grp_id in in_sync: continue
            print('add %d' % grp_id)
            cls.add(group_id, grp_id, role, session)


    @classmethod
    def add(cls, group_id, grp_id, role='C', session=None):
        assert type(group_id) == int

        if not session:
            session = get_dbhandler().session()
        if type(grp_id) == int:
            ag = cls(group_id = group_id, assoc_group_id = grp_id, role = role)
        else:
            raise RuntimeError('FATAL PROG/ERR: Need integers for all group arguments!')
            #tag = cls(group = group_id, assoc_group = grp_id, role = role)
        session.add(ag)


    @classmethod
    def remove(cls, group_id, grp_id, session):
        ag = cls.query().filter(cls.group_id == group_id, cls.assoc_group_id == grp_id).one()
        session.delete(ag)

#
# helpers
#

class UserInstance(object):

    """ UserInstance is a pickled-able instance that can be transported between processes
    """

    def __init__(self, login, id, primarygroup_id, domain=None, groups=None,
                roles=None, dbsession=None):
        """ login: string, id: int, primarygroup_id: int,
            primarygroup_id: group_id,
            groups: [ list of group_ids as Group ]
            roles: [ list of roles_ids as EK ]
        """
        assert dbsession
        self.login = login
        self.id = id
        self.domain = domain
        self.primarygroup_id = primarygroup_id
        self.groups = [ (g.name, g.id) for g in [ Group.get(gid, dbsession) for gid in groups ] ]
        self.roles = [ (EK._key(rid, dbsession=dbsession), rid) for rid in roles ]


    def in_group(self, *groups):
        """ check if user at least is in one of the groups """

        # if has SYSADM or DATAADM roles, then user is virtually part of any group
        if self.has_roles( SYSADM, DATAADM ):
            return True

        for grp in groups:
            if isinstance(grp, str):
                grp_id = Group._id( grp )
                grpname = grp
            elif isinstance(grp, int):
                grp_id = grp
                grpname = Group.get(grp_id).name
            elif isinstance(grp, Group):
                grp_id = grp.id
                grpname = grp.name
            elif isinstance(grp, tuple) and grp[1] is None:
                # force checking by name only:
                for (grpname, grp_id) in self.groups:
                    if grpname == grp[0]:
                        return True
            if (grpname, grp_id) in self.groups:
                return True
        return False

    def has_roles(self, *roles):
        """ check if user at least has one of the roles """
        for rolename in roles:
            role_id = EK._id( rolename )
            if (rolename, role_id) in self.roles:
                return True
        return False

    def get_groups(self, system=False):
        res = []
        for (grpname, gid) in self.groups:
            grp = Group.get( gid )
            if not system and grp.name.startswith('_'):
                continue
            res.append( grp )
        return res

    def check_consistency(self, update=False):
        """ check if ids of group and roles are consistent with our database,
        """
        for (grpname, gid) in self.groups:
            grp = Group.get(gid)
            if grp.name != grpname:
                raise RuntimeError('Group id: %d is not consistent!' % gid)


## globals

_DEF_USERCLASS_ = None

def set_default_userclass(userclass):
    global _DEF_USERCLASS_
    _DEF_USERCLASS_ = UserClass

def get_default_userclass():
    global _DEF_USERCLASS_
    return _DEF_USERCLASS_
