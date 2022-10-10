__copyright__ = '''
user.py - Rhombus SQLAlchemy user related module

(c) 2021 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

from .core import (registered, Column, types, Base, BaseMixIn, object_session, column_property,
                   ForeignKey, deferred, Identity, relationship, UniqueConstraint, backref,
                   column_mapped_collection, association_proxy, Table, metadata, and_,
                   NoResultFound)
from .ek import EK

from rhombus.lib.utils import get_dbhandler, cerr
from rhombus.lib.auth import authfunc
from rhombus.lib.roles import SYSADM, DATAADM, USERCLASS_MODIFY, USER_MODIFY
from passlib.hash import sha256_crypt as pwcrypt

import yaml
from pprint import pprint


@registered
class UserClass(BaseMixIn, Base):

    __tablename__ = 'userclasses'

    domain = Column(types.String(16), nullable=False, unique=True)
    desc = Column(types.String(64), nullable=False, server_default='')
    referer = Column(types.String(128), nullable=False, server_default='')
    autoadd = Column(types.Boolean, nullable=False, default=False)
    credscheme = Column(types.JSON, nullable=False, server_default='null')
    flags = Column(types.Integer, nullable=False, server_default='0')

    def __repr__(self):
        return f"UserClass({self.domain})"

    def can_modify(self, user):
        return user.has_roles(SYSADM, DATAADM, USERCLASS_MODIFY)

    @staticmethod
    def search(domain, session):
        q = session.query(UserClass).filter(UserClass.domain == domain).all()
        if q:
            return q[0]
        return None

    @staticmethod
    def allclasses():
        return [(x.id, x.domain) for x in UserClass.query().order_by(UserClass.domain).all()]

    def auth_user(self, username, passwd):
        """ return UserInstance or None """
        if not (username and passwd):
            return None

        user = User.search(username, self)
        if not user and not self.autoadd:
            return None

        # password checking performed here
        if (not user and self.autoadd) or (user and user.credential == '{X}'):
            # credential will be checked by the underlying scheme
            if type(self.credscheme) is not dict:
                raise ValueError(f'ERR: credential scheme for userclass {self.domain} '
                                 f'has not been setup!')
            if 'sys' not in self.credscheme:
                raise ValueError(f'ERR: credential scheme for userclass {self.domain} '
                                 f'does not have "sys" key!')
            ok = authfunc[self.credscheme['sys']][0](username, passwd, self.credscheme)
            if ok:
                if not user:
                    user = User(login=username, credential='{X}')
                    self.users.add(user)
                    object_session(user).flush([user])
                return user.user_instance()
        elif user and user.verify_credential(passwd):
            return user.user_instance()

        return None

    def inquire_user(self, username):
        return authfunc[self.credscheme['sys']][1](username, self.credscheme)

    def as_dict(self):
        d = super().as_dict(exclude=['users'])
        d['users'] = [u.as_dict() for u in self.users]
        return d

        return dict(id=self.id, domain=self.domain, desc=self.desc,
                    referer=self.referer, autoadd=self.autoadd,
                    credscheme=self.credscheme,
                    users=[u.as_dict() for u in self.users])

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
        uc = UserClass(domain=domain, desc=desc, referer=referer, credscheme=credscheme)
        dbsession.add(uc)
        for user in userlist:
            login, lastname, firstname, email, p_grp = user[:5]
            if len(user) >= 7:
                grps = user[6]
            else:
                grps = []
            u = uc.add_user(login, lastname, firstname, email, p_grp, grps)
            if len(user) >= 6:
                u.set_credential(user[5])

    def add_user(self, login, lastname, firstname, email, primarygroup, groups=[]):
        """ add a new user and set up the group properly, use this function
            rather than creating a new User instance for registering new users
        """

        session = object_session(self)
        if isinstance(primarygroup, Group):
            pri_grp = primarygroup
        else:
            pri_grp = Group.search(primarygroup, session)
        user_instance = User(login=login, userclass=self,
                             lastname=lastname, firstname=firstname, email=email,
                             primarygroup=pri_grp, credential='{X}')
        # set as member for primary group too
        pri_grp.users.append(user_instance)

        if groups:
            for grp in groups:
                g = Group.search(grp, session)
                if g is None:
                    raise RuntimeError('ERR: group %s does not exists!' % grp)
                g.users.append(user_instance)
        return user_instance

    def search_user(self, login):
        return User.search(login, self)

    def get_user(self, login):
        return User.search(login, self)

    @classmethod
    def from_dict(cls, d, dbh=None):
        uc = UserClass()
        uc.update(d)

        if dbh is None:
            from rhombus.lib.utils import get_dbhandler
            dbh = get_dbhandler()

        dbh.session().add(uc)
        dbh.session().flush([uc])

        if 'users' in d:
            for user_dict in d['users']:
                user = User.from_dict(user_dict, dbh, userclass=uc)

        return uc

    @staticmethod
    def dump(out, userclasses):
        """ dump data to YAML-formatted file """
        yaml.safe_dump_all((x.as_dict() for x in userclasses), out, default_flow_style=False)

    # the method below are necessary since this class is not inherited from BaseMixIn and
    # making this class inherited from BaseMixIn will introduce schema incompatibility for now

    @classmethod
    def bulk_dump_xxx(cls, dbh):
        q = cls.query(dbh.session())
        return [obj.as_dict() for obj in q]


@registered
class UserData(Base):

    __tablename__ = 'userdatas'
    id = Column(types.Integer, Identity(), primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False, index=True)
    key_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False, index=True)
    bindata = Column(types.LargeBinary, nullable=False)
    mimetype = Column(types.String(32), nullable=False)


@registered
class User(Base, BaseMixIn):

    __tablename__ = 'users'

    login = Column(types.String(32), unique=True, nullable=False)
    credential = Column(types.String(128), nullable=False)
    lastlogin = Column(types.TIMESTAMP)
    userclass_id = Column(types.Integer, ForeignKey('userclasses.id'), nullable=False,
                          index=True)
    lastname = Column(types.String(32), index=True, nullable=False)
    firstname = Column(types.String(32), nullable=False, server_default='')
    fullname = column_property(lastname + ', ' + firstname)

    # email is unique because it can be used to authenticate user as well
    email = Column(types.String(32), unique=True, nullable=False)
    email2 = Column(types.String(64), index=True, nullable=False, server_default='')
    institution = Column(types.String(64), nullable=False, server_default='')
    address = Column(types.String(128), nullable=False, server_default='')
    contact = Column(types.String(64), nullable=False, server_default='')
    status = Column(types.String(1), nullable=False, server_default='A')
    flags = Column(types.Integer, nullable=False, server_default='0')

    primarygroup_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False, index=True)

    json = deferred(Column(types.JSON, nullable=False, server_default='null'))

    __table_args__ = (UniqueConstraint('login', 'userclass_id'), {})

    userclass = relationship(UserClass, uselist=False, foreign_keys=userclass_id,
                             backref=backref('users', lazy='dynamic'))
    primarygroup = relationship('Group', uselist=False, foreign_keys=primarygroup_id,
                                backref=backref('primaryusers'))
    userdata = relationship(UserData,
                            collection_class=column_mapped_collection(UserData.key_id),
                            cascade='all,delete,delete-orphan')
    groups = association_proxy('usergroups', 'group')

    def __init__(self, *args, **kwargs):
        self.credential = '{X}'
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{self.login}/{self.userclass.domain}"

    def __repr__(self):
        return "%s/%s" % (self.login, str(self.userclass).lower())

    def can_modify(self, user):
        return (user.has_roles(SYSADM, DATAADM, USER_MODIFY) or user.id == self.id)

    def get_login(self):
        return "%s/%s" % (self.login, self.userclass.domain)

    def update(self, obj):

        super().update(obj, exclude=['primarygroup_id'])

        if isinstance(obj, dict):
            if 'primarygroup_id' in obj:
                self.set_primarygroup(obj['primarygroup_id'])
        else:
            if obj.primarygroup_id:
                self.set_primarygroup(obj.primarygroup_id)

        return self

    def set_primarygroup(self, grp):

        # assert self.id
        if type(grp) == int:
            primarygroup_id = grp
        else:
            primarygroup_id = grp.id

        session = object_session(self) or get_dbhandler().session()

        if self.primarygroup_id and self.id is not None:
            if self.primarygroup_id == primarygroup_id:
                return

            # remove from previous group
            UserGroup.delete(session, self.id, self.primarygroup_id)

        self.primarygroup_id = primarygroup_id
        UserGroup.add(session, self, primarygroup_id)

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
        if r:
            return r[0]
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
        """return a list of group_ids where this user is member of"""
        dbsession = object_session(self)
        grp_ids = [x[0] for x in dbsession.query(UserGroup.group_id)
                   .filter(UserGroup.user_id == self.id)]
        grp_ids2 = [x[0] for x in dbsession.query(AssociatedGroup.group_id)
                    .filter(AssociatedGroup.assoc_group_id.in_(grp_ids))]
        return set(grp_ids + grp_ids2)

    def group_role_ids(self):
        """return list of (grp_ids, role_ids) on all available groups and roles"""
        dbsession = object_session(self)
        grp_ids = self.groupids()
        res = dbsession.execute(
            group_role_table.select(group_role_table.c.group_id.in_(grp_ids))
            .with_only_columns([group_role_table.c.role_id]).distinct())
        role_ids = [item for sublist in res.fetchall() for item in sublist]
        return (grp_ids, role_ids)

    def group_users(self):
        dbsession = object_session(self)
        if self.has_roles(SYSADM):
            return User.query(dbsession).all()
        group_ids = self.groupids()
        user_ids = [x.user_id for x in UserGroup.query(dbsession)
                    .filter(UserGroup.group_id.in_(group_ids))]
        return [User.get(u, dbsession) for u in set(user_ids)]

    def has_roles(self, *roles):
        grp_ids, role_ids = self.group_role_ids()
        dbsess = object_session(self)
        for role in roles:
            role_id = EK._id(role, grp='@ROLES', dbsession=dbsess)
            if role_id in role_ids:
                return True
        return False

    def user_instance(self):
        group_ids, role_ids = self.group_role_ids()
        return UserInstance(self.login, self.id, self.primarygroup_id,
                            self.userclass.domain, group_ids, role_ids,
                            dbsession=object_session(self))

    def render(self):
        return "%s | %s" % (str(self), self.fullname)

    def as_dict(self, exclude=[]):
        # we will handle primarygroup using name, so primarygroup_id is excluded
        d = super().as_dict(exclude=exclude + ['primarygroup_id', 'usergroups', 'userdata'])
        d['primarygroup'] = self.primarygroup.name
        d['groups'] = [[ug.group.name, ug.role] for ug in self.usergroups]
        return d

    def set_credential(self, passwd):
        if passwd == '{X}':
            self.credential = passwd
        else:
            self.credential = pwcrypt.encrypt(passwd)

    def verify_credential(self, passwd):
        if self.credential == '{X}':
            raise RuntimeError('this password use external system')
        return pwcrypt.verify(passwd, self.credential)

    def sync_groups(self, in_groups, out_groups):
        """ synchronize user's group with groups """
        dbsession = object_session(self)
        added = []
        removed = []
        modified = []
        current_groups = {}
        for grp in self.groups:
            current_groups[grp.name] = grp

        current_usergroups = {}
        for ug in self.usergroups:
            current_usergroups[ug.group.name] = ug

        # check-in or modify for in_groups
        for g in in_groups:
            grp = Group.search(g, dbsession)
            if grp is None:
                continue
            if g in current_usergroups:
                if in_groups[g] == current_usergroups[g].role:
                    continue
                current_usergroups[g].role = in_groups[g]
                modified.append(g)
                continue

            UserGroup.add(dbsession, self, grp, in_groups[g])
            added.append(g)

        # check-out for out_groups
        for g in out_groups:
            grp = Group.search(g, dbsession)
            if grp is None:
                continue
            if g in current_usergroups:
                UserGroup.delete(dbsession, self.id, grp.id)
                removed.append(g)

        return added, modified, removed

    @classmethod
    def from_dict(cls, d, dbh, userclass=None):

        session = dbh.session()

        # we add user to primarygroup after after flushing to obtain user.id
        if 'primarygroup_id' in d:
            del d['primarygroup_id']

        obj = super().from_dict(d, dbh)
        obj.userclass = userclass
        with session.no_autoflush:
            if 'primarygroup' in d:
                obj.primarygroup_id = Group.search(d['primarygroup'], session).id

        # we need to flush to db to get user.id
        session.flush([obj])

        cerr(f'[New user login: {obj.login} id: {obj.id}] with '
             f'primarygroup id: {obj.primarygroup_id}')

        # add to all groups, including primary group
        groups = d['groups']
        if groups:
            with session.no_autoflush:
                for grp in groups:
                    cerr(f'[Adding user {obj.id}/{obj.login} to group {grp}]')
                    g = Group.search(grp[0], session)
                    if g is None:
                        raise RuntimeError('ERR: group %s does not exists!' % grp)
                    ug = dbh.UserGroup(obj, g, grp[1])
                    session.flush([ug])
        return obj

    @staticmethod
    def dump(out, query=None):
        import yaml
        if not query:
            query = User.query()
        yaml.dump_all((x.as_dict() for x in query), out, default_flow_style=False)


def _create_ug_by_user(user):
    return UserGroup(user=user)


group_role_table = Table(
    'groups_roles', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('group_id', types.Integer, ForeignKey('groups.id'), nullable=False),
    Column('role_id', types.Integer, ForeignKey('eks.id'), nullable=False),
    UniqueConstraint('group_id', 'role_id')
)


@registered
class Group(Base, BaseMixIn):

    __tablename__ = 'groups'

    name = Column(types.String(32), nullable=False, unique=True)
    desc = Column(types.String(128), nullable=False, server_default='')
    scheme = deferred(Column(types.JSON, nullable=False, server_default='null'))
    flags = Column(types.Integer, nullable=False, server_default='0', default=0)

    users = association_proxy('usergroups', 'user', creator=_create_ug_by_user)
    roles = relationship(EK, secondary=group_role_table, order_by=EK.key)

    # flags
    f_composite_group = 1 << 0

    def __repr__(self):
        return "<Group: %s>" % self.name

    def __str__(self):
        return self.name

    def has_member(self, user):
        if type(user) == int:
            if (self.flags & self.f_composite_group):
                # join UserGroup and AssociatedGroup
                user_ids = [x[0] for x in
                            list(AssociatedGroup.get_usergroup_info_query(self, 'C'))]
            else:
                user_ids = [x[0] for x in
                            object_session(self).query(UserGroup.user_id)
                            .filter(UserGroup.group_id == self.id)
                            ]
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
            uginfo = AssociatedGroup.get_usergroup_info_query(self, 'C').filter(
                UserGroup.user_id == user_id).one()
            if uginfo and uginfo[1] == 'A':
                return True
            return False

        try:
            sess = object_session(self)
            ug = UserGroup.query(sess).filter(UserGroup.group_id == self.id,
                                              UserGroup.user_id == user_id).one()
            if ug and ug.role == 'A':
                return True
        except NoResultFound:
            pass

        return False

    def check_flags(self, flag):
        return self.flags & flag

    def set_flags(self, flag, val):
        self.flags = (self.flags | flag) if val is True else (self.flags & ~flag)

    def render(self):
        if self.desc:
            return "%s | %s" % (self.name, self.desc)
        return self.name

    @staticmethod
    def search(grpname, dbsession):
        if type(grpname) == int:
            return Group.get(grpname, dbsession)
        q = Group.query(dbsession).filter(Group.name == grpname).all()
        if q:
            return q[0]
        return None

    @staticmethod
    def _id(grpname, dbsession):
        assert dbsession
        grp = Group.search(grpname, dbsession=dbsession)
        if grp:
            return grp.id
        return 0

    @staticmethod
    def _name(grpid, dbsession):
        assert dbsession
        grp = Group.get(grpid, dbsession)
        if grp:
            return grp.name
        return None

    @staticmethod
    def bulk_insert(grplist, dbsession):
        """ grplist = [ (grpname, desc, role_list) ] """
        print(grplist)
        for grpitem in grplist:
            if len(grpitem) == 3:
                grpname, desc, roles = grpitem[0], grpitem[1], grpitem[2]
            else:
                grpname, desc, roles = grpitem[0], grpitem[0], grpitem[1]
            grp = Group(name=grpname, desc=desc)
            dbsession.add(grp)
            for role in roles:
                grp.roles.append(EK.search(role, dbsession=dbsession))

    def update(self, obj):
        if type(obj) == dict:

            self.update_fields_with_dict(obj)

            # flags
            if 'flags-on' in obj:
                self.flags |= obj['flags-on']
            if 'flags-off' in obj:
                self.flags &= ~ obj['flags-off']

            if 'composite_ids' in obj:
                if not self.id:
                    # this is new object, so we can just attach using SqlAlchemy's
                    # relationship mechanism
                    session = get_dbhandler().session()
                    with session.no_autoflush:
                        for ag_id in obj['composite_ids']:
                            AssociatedGroup.add(self, ag_id, 'C', session)
                else:
                    sess = object_session(self)
                    composite_ids = obj['composite_ids']
                    AssociatedGroup.sync(self.id, composite_ids, session=sess)

        else:
            self.update_fields_with_object(obj)

    def as_dict(self):
        d = self.create_dict_from_fields(exclude=['users', 'associated_groups',
                                                  'primaryusers', 'usergroups'])
        d['users'] = [[ug.user.login, ug.role] for ug in self.usergroups]
        d['roles'] = [ek.key for ek in self.roles]
        if (self.flags & self.f_composite_group):
            d['assoc_groups'] = [[x.associated_group.name, x.role]
                                 for x in AssociatedGroup.query(object_session(self))
                                 .filter(AssociatedGroup.group_id == self.id)]
        return d

    @classmethod
    def from_dict(cls, d, dbh):
        obj = super().from_dict(d, dbh)
        dbsess = dbh.session()
        for role in d['roles']:
            obj.roles.append(EK.search(role, dbsession=dbsess))
        for assoc_group in d.get('assoc_groups', []):
            g = dbh.get_group(assoc_group[0])
            ag = AssociatedGroup(group_id=obj.id, assoc_group_id=g.id, role=assoc_group[1])
            dbsess.add(ag)

        return obj

    @staticmethod
    def dump(out, query=None):
        if query is None:
            query = Group.query()
        yaml.safe_dump_all((x.as_dict() for x in query), out, default_flow_style=False)

    # the method below are necessary since this class is not inherited from BaseMixIn and
    # making this class inherited from BaseMixIn will introduce schema incompatibility for now

    @classmethod
    def bulk_dump(cls, dbh):
        q = cls.query(dbh.session())
        return [obj.as_dict() for obj in q]


@registered
class UserGroup(Base):

    __tablename__ = 'users_groups'
    id = Column(types.Integer, Identity(), primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    role = Column(types.String(1), nullable=False, server_default='M')
    # M: member, A: administrator

    __table_args__ = (UniqueConstraint('user_id', 'group_id'), {})

    user = relationship(User, uselist=False,
                        backref=backref('usergroups', cascade='all,delete,delete-orphan'))
    group = relationship(Group, uselist=False,
                         backref=backref('usergroups', cascade='all,delete,delete-orphan'))

    def __init__(self, user=None, group=None, role=None):
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
        session.add(ug)

    @staticmethod
    def delete(session, user_id, group_id):
        ug = UserGroup.query(session).filter(UserGroup.user_id == user_id,
                                             UserGroup.group_id == group_id).one()
        session.delete(ug)


@registered
class AssociatedGroup(Base):

    __tablename__ = 'associated_groups'
    id = Column(types.Integer, Identity(), primary_key=True)
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    assoc_group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    role = Column(types.String(1), nullable=False, server_default='R')
    # R: ?, C: composite member

    group = relationship(Group, uselist=False, foreign_keys=[group_id],
                         backref=backref('associated_groups',
                                         cascade='all,delete,delete-orphan'))
    associated_group = relationship(Group, uselist=False, foreign_keys=[assoc_group_id])

    __table_args__ = (UniqueConstraint('group_id', 'assoc_group_id'), {})

    @classmethod
    def get_usergroup_info_query(cls, group, role=None):
        """ return tuples of (user_id, group_id, role) for those associated with the group
        """
        q = object_session(group).query(
            UserGroup.user_id, UserGroup.role, UserGroup.group_id, cls.role
        ).filter(UserGroup.group_id == cls.assoc_group_id, cls.group_id == group.id)
        if role:
            q = q.filter(cls.role == role)
        return q

    @classmethod
    def sync(cls, group_id, group_ids, role='C', session=None):
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
                in_sync.append(ag.assoc_group_id)
            else:
                # remove this tag
                session.delete(ag)

        print(in_sync)
        for grp_id in group_ids:
            if grp_id in in_sync:
                continue
            print('add %d' % grp_id)
            cls.add(group_id, grp_id, role, session)

    @classmethod
    def add(cls, group_id, grp_id, role='C', session=None):

        if not session:
            session = get_dbhandler().session()

        ag = Group.get(grp_id, session)
        if (ag.flags & ag.f_composite_group):
            raise RuntimeError(
                'Error: composite group cannot consist of another composite group!')
        if type(group_id) == int:
            ag = cls(group_id=group_id, assoc_group_id=grp_id, role=role)
        elif isinstance(group_id, Group):
            ag = cls(group=group_id, assoc_group_id=grp_id, role=role)
        else:
            raise RuntimeError('FATAL PROG/ERR: Need integer or group for 1st argument')
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
        self.groups = [(g.name, g.id) for g in [Group.get(gid, dbsession) for gid in groups]]
        self.roles = [(EK._key(rid, dbsession=dbsession), rid) for rid in roles]
        self.laststamp = -1

    def __str__(self):
        return f"{self.login}/{self.domain}"

    def is_sysadm(self):
        return self.has_roles(SYSADM, DATAADM)

    def is_admin(self, * additional_roles):
        return self.has_roles(* [SYSADM, DATAADM] + list(additional_roles))

    def in_group(self, *groups):
        """ check if user at least is in one of the groups """

        # if has SYSADM or DATAADM roles, then user is virtually part of any group
        if self.has_roles(SYSADM, DATAADM):
            return True

        for grp in groups:
            if isinstance(grp, str):
                grp_id = Group._id(grp)
                grpname = grp
            elif isinstance(grp, int):
                grp_id = grp
                grpname = Group._name(grp_id, get_dbhandler().session())
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
        dbsess = get_dbhandler().session()
        for rolename in roles:
            role_id = EK._id(rolename, grp='@ROLES', dbsession=dbsess)
            if (rolename, role_id) in self.roles:
                return True
        return False

    def get_groups(self, dbsession, system=False):
        """return all groups where this user belongs to"""
        res = []
        system = system or self.is_sysadm()
        for (grpname, gid) in self.groups:
            if (grp := Group.get(gid, dbsession)) is None:
                # the group might have been removed during after this user has logged in,
                # so just skip
                continue
            if not system and grp.name.startswith('_'):
                continue
            res.append(grp)
        return res

    def check_consistency(self, update=False):
        """ check if ids of group and roles are consistent with our database,
        """
        for (grpname, gid) in self.groups:
            grp = Group.get(gid)
            if grp.name != grpname:
                raise RuntimeError('Group id: %d is not consistent!' % gid)


#
# globals
#

_DEF_USERCLASS_ = None


def set_default_userclass(userclass):
    global _DEF_USERCLASS_
    _DEF_USERCLASS_ = UserClass


def get_default_userclass():
    global _DEF_USERCLASS_
    return _DEF_USERCLASS_

# EOF
