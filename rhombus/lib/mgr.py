
import sys
import yaml
import transaction
import os.path
from rhombus.lib.utils import get_dbhandler, cerr, cout, cexit
from rhombus.scripts import setup_settings, arg_parser

# rbmgr.py
#
# this command manages datatype directly related to rhombus only
# ie: userclass, user, group, enumkey


def init_argparser(parser=None):

    if parser is None:
        p = arg_parser('rbmgr [rhombus]')
    else:
        p = parser

    # commands

    p.add_argument('--initdb', action='store_true', default=False,
                   help='initialize database')

    # import/export to YAML

    p.add_argument('--importuserclass', default=False, action='store_true',
                   help='import userclass from YAML file')

    p.add_argument('--exportuserclass', default=False, action='store_true',
                   help='export userclass to YAML file')
    # exported YAML file need to contain certain field for format recognizition

    p.add_argument('--importgroup', default=False,
                   help='import group from YAML file')

    p.add_argument('--exportgroups', default=False, action='store_true',
                   help='export group from YAML file')

    p.add_argument('--importenumkey', default=False,
                   help='import enumerated key from YAML file')

    p.add_argument('--exportenumkey', default=False,
                   help='export enumerated key to YAML file')

    p.add_argument('--listuserclass', default=False, action='store_true',
                   help='list user class(es)')

    p.add_argument('--listuser', default=False, action='store_true',
                   help='list user(s) from a userclass')

    p.add_argument('--listgroup', default=False, action='store_true',
                   help='list all groups')

    # ekeys

    p.add_argument('--listenumkey', default=False, action='store_true')
    p.add_argument('--addenumkey', default=False)
    p.add_argument('--delenumkey', default=False)

    # dump/load all

    p.add_argument('--rbdump', default=False, action='store_true')
    p.add_argument('--rbload', default=False, action='store_true')

    # direct manipulation

    p.add_argument('--adduser', action='store_true', default=False,
                   help='add a new user')

    p.add_argument('--setcred', action='store_true', default=False,
                   help='change user credential')

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
    p.add_argument('--inquire', default=False, action='store_true')

    p.add_argument('--ekeygroup', default=None)

    # general options here

    p.add_argument('--infile', default='-')
    p.add_argument('--outfile', default='-')

    p.add_argument('--indir')
    p.add_argument('--outdir')

    return db_argparser(p)


def db_argparser(p):

    # all db-related options here

    p.add_argument('-c', '--config', default=False,
                   help='config file (or use RHOMBUS_CONFIG environment)')

    p.add_argument('--commit', action='store_true', default=False,
                   help='commit the changes to database')

    p.add_argument('--rollback', action='store_true', default=False,
                   help='do no commit the changes and rollback the database')

    return p


def main(args):

    settings = setup_settings(args)

    if any((args.exportuserclass, args.exportgroups, args.exportenumkey)):
        do_rbmgr(args, settings)

    elif not args.rollback and (args.commit or args.initdb):
        with transaction.manager:
            do_rbmgr(args, settings)
            cerr('** COMMIT database **')

    else:
        cerr('** WARNING -- running without database COMMIT **')
        if not args.rollback:
            keys = input('Do you want to continue? ')
            if keys.lower()[0] != 'y':
                sys.exit(1)
        do_rbmgr(args, settings)


def do_rbmgr(args, settings, dbh=None):

    if not dbh:
        dbh = get_dbhandler(settings, initial=args.initdb)

    if args.initdb:
        do_initdb(args, dbh, settings)

    elif args.adduser:
        do_adduser(args, dbh, settings)

    elif args.setcred:
        do_setcred(args, dbh, settings)

    elif args.importgroup:
        do_importgroup(args, dbh, settings)

    elif args.exportgroups:
        do_exportgroups(args, dbh, settings)

    elif args.exportenumkey:
        do_exportenumkey(args, dbh, settings)

    elif args.importenumkey:
        do_importenumkey(args, dbh, settings)

    elif args.listenumkey:
        do_listenumkey(args, dbh, settings)

    elif args.addenumkey:
        do_addenumkey(args, dbh, settings)

    elif args.listuserclass:
        do_listuserclass(args, dbh, settings)

    elif args.listuser:
        do_listuser(args, dbh, settings)

    elif args.listgroup:
        do_listgroup(args, dbh, settings)

    elif args.exportuserclass:
        do_exportuserclass(args, dbh, settings)

    elif args.importuserclass:
        do_importuserclass(args, dbh, settings)

    elif args.rbdump:
        do_rbdump(args, dbh, settings)

    elif args.rbload:
        do_rbload(args, dbh, settings)

    else:
        return False

    return True


def do_initdb(args, dbh, settings):

    print('do_initdb()')

    dbh.initdb(create_table=(not args.no_create_table),
               init_data=(not args.no_init_data),
               rootpasswd=args.credential or None)
    from rhombus.scripts.setup import populate_db
    userclass = yaml.load(open(args.initial_userclass)) if args.initial_userclass else None
    groups = yaml.load(open(args.initial_groups)) if args.initial_groups else None
    populate_db(dbh.session(), groups, userclass)
    cout('INFO - database has been initialized')


def do_adduser(args, dbh, settings):

    print('do_adduser()')

    if not args.userclass:
        cexit('ERR - please provide userclass')
    domain = dbh.get_userclass(args.userclass)
    if not domain:
        cexit('ERR - userclass: %s does not exist!' % args.userclass)

    if not args.login:
        cexit('ERR - please provide login name')

    if args.inquire:
        # get user detail remotely
        args.lastname, args.firstname, args.email = domain.inquire_user(args.login)
        if not args.lastname:
            cexit('ERR - cannot inquire username: %s' % args.login)
        cerr('Obtaining: %s, %s [%s]' % (args.lastname, args.firstname, args.email))

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

    user = domain.add_user(login=args.login, email=args.email,
                           lastname=args.lastname, firstname=args.firstname,
                           primarygroup=args.primarygroup,
                           groups=groups)

    cout('User %s added sucessfully.' % user.login)


# # ENUM KEY


def do_setcred(args, dbh, settings):

    if '/' in args.login:
        args.login, args.userclass = args.login.split('/', 1)

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

    ekeys = dbh.list_ekeys(group=args.ekeygroup)
    for ek in ekeys:
        cout('%s' % ek.key)


def do_exportenumkey(args, dbh, settings):

    cerr('Exporting enumkey')
    ekey_list = []
    ekeys = []
    if args.exportenumkey:
        for ekey_code in args.exportenumkey.split(','):
            cerr('Getting [%s]' % ekey_code)
            ekeys.append(dbh.get_ekey(ekey_code))
    else:
        ekeys = dbh.list_ekeys()

    for ekey in ekeys:
        ekey_list.append(ekey.as_dict())

    if args.outfile != '-':
        open(args.outfile, 'w').write(yaml.dump(ekey_list))


def do_importenumkey(args, dbh, settings):

    cerr('Importing enumkey')
    ekeys = yaml.load(open(args.infile))
    for ek_data in ekeys:
        dbh.EK.from_dict(ek_data, False, dbh.session())


def do_importgroup(args, dbh, settings):

    cerr('Importing group')
    groups = yaml.load(open(args.importgroup))

    from rhombus.models.user import Group

    Group.bulk_insert(groups, dbsession=dbh.session())


def do_listuserclass(args, dbh, settings):

    cerr('List user class(es):')

    for uc in dbh.UserClass.query(dbh.session()):
        cout(' %s' % uc.domain)


def do_listuser(args, dbh, settings):

    if not args.userclass:
        cexit('ERR: Please provide --userclass')

    cerr('List user from user class: %s' % args.userclass)

    for u in dbh.get_userclass(args.userclass).users:
        cout(' %s' % u.login)


def do_listgroup(args, dbh, settings):

    for g in dbh.Group.query(dbh.session()).all():
        cout(f' {g.name}')


def do_exporteks(args, dbh, settings):
    yaml_write(args, dbh.EK.bulk_dump(dbh), 'EK')


def do_importeks(args, dbh, settings):
    yaml_read(args, dbh, dbh.EK)


def do_exportgroups(args, dbh, settings):
    yaml_write(args, dbh.Group.bulk_dump(dbh), 'Group')


def do_importgroups(args, dbh, settings):
    yaml_read(args, dbh, dbh.Group)


def do_exportuserclass(args, dbh, settings):

    userclasses = None
    if args.userclass:
        userclasses = dbh.get_userclass([args.userclass])
    yaml_write(args, dbh.UserClass.bulk_dump(dbh, userclasses), 'UserClass')


def do_importuserclass(args, dbh, settings):
    yaml_read(args, dbh, dbh.UserClass)


def do_rbdump(args, dbh, settings):
    """ this function will dump all Rhombus core data to YAML file """

    args.outfile = os.path.join(args.outdir, 'eks.yaml')
    do_exporteks(args, dbh, settings)

    args.outfile = os.path.join(args.outdir, 'groups.yaml')
    do_exportgroups(args, dbh, settings)

    args.outfile = os.path.join(args.outdir, 'userclasses.yaml')
    do_exportuserclass(args, dbh, settings)

    return

    d = {}
    # dump EK first
    d['_Rb_:EK'] = dbh.EK.bulk_dump(dbh)
    d['_Rb_:UserClass'] = dbh.UserClass.bulk_dump(dbh)
    d['_Rb_:Group'] = dbh.Group.bulk_dump(dbh)
    yaml.safe_dump(d, open(args.outfile, 'w'), default_flow_style=False)


def do_rbload(args, dbh, settings):
    """ this function will load all Rhombus core data from YAML file """

    args.infile = os.path.join(args.indir, 'eks.yaml')
    do_importeks(args, dbh, settings)
    dbh.session().flush()

    args.infile = os.path.join(args.indir, 'groups.yaml')
    do_importgroups(args, dbh, settings)
    dbh.session().flush()

    args.infile = os.path.join(args.indir, 'userclasses.yaml')
    do_importuserclass(args, dbh, settings)
    dbh.session().flush()

    return

    d = yaml.load(open(args.infile, 'r'))

    # set EK
    dbh.EK.bulk_load(d['_Rb_:EK'], dbh)
    dbh.session().flush()

    # set groups
    dbh.Group.bulk_load(d['_Rb_:Group'], dbh)
    dbh.session().flush()

    # set userclass and user
    dbh.UserClass.bulk_load(d['_Rb_:UserClass'], dbh)


def do_syncuserclass(args, dbh, settings):

    if not args.userclass:
        cexit('ERR: Please provide --userclass')

    if not args.synctoken:
        cexit('ERR: Please provide --synctoken')

    raise NotImplementedError('This functionality has not been implemented.')


def yaml_write(args, data, msg, printout=False):
    if printout:
        # this is for debugging purpose, obviously
        import pprint
        for d in data:
            pprint.pprint(d)
            pprint.pprint(yaml.dump(d))
    with open(args.outfile, 'w') as outstream:
        yaml.dump_all(data, outstream, default_flow_style=False)
    cerr(f'[Exported {msg} to {args.outfile}]')


def yaml_read(args, dbh, class_):
    # yaml.safe_load_all is a generator
    with open(args.infile, 'r') as instream:
        class_.bulk_load(yaml.safe_load_all(instream), dbh)
    cerr(f'[Imported {class_.__name__} from {args.infile}')

# end of file
