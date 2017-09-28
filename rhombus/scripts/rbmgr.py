
import sys, yaml, transaction
from rhombus.lib.utils import get_dbhandler, cerr, cout, cexit
from rhombus.scripts import setup_settings, arg_parser

## rbmgr.py
##
## this command manages datatype directly related to rhombus only
## ie: userclass, user, group, enumkey


def init_argparser( parser = None):

    if parser is None:
        p = arg_parser('rbmgr [rhombus]')
    else:
        p = parser

    # commands

    p.add_argument('--initdb', action='store_true', default=False,
        help = 'initialize database')


    # import/export to YAML

    p.add_argument('--importuserclass', default=False,
        help = 'import userclass from YAML file')

    p.add_argument('--exportuserclass', default=False,
        help = 'export userclass to YAML file')
    # exported YAML file need to contain certain field for format recognizition

    p.add_argument('--importgroup', default=False,
        help = 'import group from YAML file')

    p.add_argument('--exportgroup', default=False,
        help = 'export group from YAML file')

    p.add_argument('--importenumkey', default=False,
        help = 'import enumerated key from YAML file')

    p.add_argument('--exportenumkey', default=False,
        help = 'export enumerated key to YAML file')

    p.add_argument('--listuserclass', default=False, action='store_true',
        help = 'list user class(es)')

    p.add_argument('--listuser', default=False, action='store_true',
        help = 'list user(s) from a userclass')

    # ekeys

    p.add_argument('--listenumkey', default=False, action='store_true')
    p.add_argument('--addenumkey', default=False)
    p.add_argument('--delenumkey', default=False)

    # direct manipulation

    p.add_argument('--adduser', action='store_true', default=False,
        help = 'add a new user')

    p.add_argument('--setcred', action='store_true', default=False,
        help = 'change user credential')


    # specific options

    p.add_argument('--no-create-table', default=False, action='store_true')
    p.add_argument('--no-init-data', default=False, action='store_true')

    p.add_argument('--initial_userclass', default=False)
    p.add_argument('--initial_groups', default=False)

    p.add_argument('--login', default='')
    p.add_argument('--primarygroup', default='')
    p.add_argument('--lastname', default='')
    p.add_argument('--firstname', default='')
    p.add_argument('--userclass', default='')
    p.add_argument('--email', default='')
    p.add_argument('--groups', default='')
    p.add_argument('--credential', default='')

    p.add_argument('--ekeygroup', default=None)

    # general options here

    return db_argparser(p)


def db_argparser( p ):

    # all db-related options here

    p.add_argument('-c', '--config', default=False,
        help = 'config file (or use RHOMBUS_CONFIG environment)')

    p.add_argument('--commit', action='store_true', default=False,
        help = 'commit the changes to database')

    p.add_argument('--rollback', action='store_true', default=False,
        help = 'do no commit the changes and rollback the database')

    return p



def main(args):

    settings = setup_settings( args )

    if any( (args.exportuserclass, args.exportgroup, args.exportenumkey) ):
        do_rbmgr( args, settings )

    elif not args.rollback and (args.commit or args.initdb):
        with transaction.manager:
            do_rbmgr( args, settings )
            cerr('** COMMIT database **')

    else:
        cerr('** WARNING -- running without database COMMIT **')
        if not args.rollback:
            keys = input('Do you want to continue? ')
            if keys.lower()[0] != 'y':
                sys.exit(1)
        do_rbmgr( args, settings )



def do_rbmgr(args, settings, dbh = None):

    if not dbh:
        dbh = get_dbhandler(settings, initial = args.initdb)

    if args.initdb:
        do_initdb(args, dbh, settings)

    elif args.adduser:
        do_adduser(args, dbh, settings)

    elif args.setcred:
        do_setcred(args, dbh, settings)

    elif args.importgroup:
        do_importgroup(args, dbh, settings)

    elif args.listenumkey:
        do_listenumkey(args, dbh, settings)

    elif args.addenumkey:
        do_addenumkey(args, dbh, settings)

    elif args.listuserclass:
        do_listuserclass(args, dbh, settings)

    elif args.listuser:
        do_listuser(args, dbh, settings)

    else:
        return False

    return True



def do_initdb(args, dbh, settings):

    print('do_initdb()')

    dbh.initdb(create_table = (not args.no_create_table),
            init_data = (not args.no_init_data))
    from rhombus.scripts.setup import populate_db
    userclass = yaml.load(open(args.initial_userclass)) if args.initial_userclass else None
    groups = yaml.load(open(args.initial_groups)) if args.initial_groups else None
    populate_db(dbh.session(), groups, userclass)
    cout('INFO - database has been initialized')


def do_adduser(args, dbh, settings):

    print('do_adduser()')

    if not args.userclass:
        cexit('ERR - please provide userclass')
    domain = dbh.get_userclass( args.userclass )
    if not domain:
        cexit('ERR - userclass: %s does not exist!' % args.userclass)

    if not args.login:
        cexit('ERR - please provide login name')

    if not args.lastname:
        cexit('ERR - please provide last name')

    if not args.firstname:
        cexit('ERR - please provide firstname')

    if not args.email:
        cexit('ERR - please provide email address')

    if not args.primarygroup:
        cexit('ERR - please provide primarygroup')

    if args.groups:
        groups = args.groups.split(',')
    else:
        groups = []

    user = domain.add_user( login = args.login, email = args.email,
                            lastname = args.lastname, firstname = args.firstname,
                            primarygroup = args.primarygroup,
                            groups = groups, session = dbh.session() )

    cout('User %s added sucessfully.' % user.login)


## ENUM KEY



def do_setcred(args, dbh, settings):

    if not args.userclass:
        cexit('ERR - please provide userclass')

    if not args.login:
        cexit('ERR - please provide login name')

    domain = dbh.get_userclass(args.userclass)
    user = domain.search_user(args.login)

    if not user:
        cexit('WARN - user does not exist')

    if args.credential:
        user.set_credential(args.credential)
        cerr('Credential for user %s has been modified sucessfully' % user.login)


def do_addenumkey(args, dbh, settings):

    cerr('Add enumkey')

    key = args.addenumkey
    key = key.upper() if key.startswith('@') else key.lower()

    key_group = args.ekeygroup
    if key_group is None and not key.startswith('@'):
        cexit('ekey must under a group, or a group key which starts with @')

    ekey = dbh.add_ekey(key, key_group)
    cerr('I - enumkey: %s / %s has been added.' %
        (ekey.key, ekey.group.key if ekey.group else '*'))


def do_listenumkey(args, dbh, settings):

    cerr('List enumkey')

    ekeys = dbh.list_ekeys(group = args.ekeygroup)
    for ek in ekeys:
        cout('%s' % ek.key)


def do_importgroup(args, dbh, settings):

    cerr('Importing group')
    groups = yaml.load(open(args.importgroup))

    from rhombus.models.user import UserClass, Group

    Group.bulk_insert(groups, dbsession=dbh.session())


def do_listuserclass(args, dbh, settings):

    cerr('List user class(es):')

    for uc in dbh.UserClass.query(dbh.session()):
        cout(' %s' % uc.domain)


def do_listuser(args, dbh, settings):

    cerr('List user from user class: %s' % args.userclass)

    for u in dbh.get_userclass(args.userclass).users:
        cout(' %s' % u.login)
