
from rhombus.models.ek import EK
from rhombus.models.user import Group, UserClass
from rhombus.models.filemgr import File
from rhombus.models.core import get_clsreg
from rhombus.models.meta import get_datalogger
from rhombus.lib.roles import *
from rhombus.lib.utils import random_string, cerr
import transaction

def setup_db( *ops ):
    """ setup the database (create tables, etc) and populate with basic data """

    base = get_base()

    # WARN: use alembic to create initial tables
    #base.metadata.create_all()

    with transaction.manager:
        if get_datalogger():
            get_clsreg().sync()

    with transaction.manager:
        EK.bulk_insert( ek_initlist )
        Group.bulk_insert( essential_groups )

        file = File( path='/', type='file/folder', mimetype='application/x-directory',
                    group_id = Group._id('_SysAdm_'), permanent = True )
        dbsession.add( file )

        for op in ops:
            op()

def setup( dbh, rootpasswd=None ):
    """ populate the database with basic, essential data """

    global root_password

    if get_datalogger():
        get_clsreg().sync()
        session.commit()

    dbsession = dbh.session()

    EK.bulk_update( ek_initlist, dbsession=dbsession )
    Group.bulk_insert( essential_groups, dbsession=dbsession )
    UserClass.bulk_insert( system_userclass, dbsession=dbsession )

    group_id = Group._id('_SysAdm_', dbsession)
    file = File( path='/', group_id = group_id, permanent = True )
    dbsession.add( file )
    file.type = 'file/folder'
    file.mimetype = 'application/x-directory'

    if rootpasswd:
        # set system password

        sysuser = dbh.get_user('system/_SYSTEM_')
        sysuser.set_credential(rootpasswd)
        root_password = rootpasswd

    cerr('INFO: root password is %s\n' % root_password)


root_password = random_string(16)
system_userclass = ( '_SYSTEM_', 'Rhombus System', None, {},
                        [   ('system', '', '', 'system@localhost', '_SysAdm_', root_password, [] ),
                            ('dataadm', '', '', 'dataadm@localhost', '_DataAdm_', '{X}', [] ),
                        ] )


essential_groups = [
            ( '__default__', [ PUBLIC ] ),
            ( '_SysAdm_', [SYSADM, SYSVIEW] ),
            ( '_EKMgr_', [ EK_CREATE, EK_MODIFY, EK_DELETE, EK_VIEW ] ),
            ( '_UserClassMgr_', [ USERCLASS_CREATE, USERCLASS_MODIFY, USERCLASS_DELETE, USERCLASS_VIEW ] ),
            ( '_UserMgr_', [ USER_CREATE, USER_MODIFY, USER_DELETE, USER_VIEW ] ),
            ( '_GroupMgr_', [ GROUP_CREATE, GROUP_MODIFY, GROUP_DELETE,
                                GROUP_ADDUSER, GROUP_DELUSER, GROUP_VIEW ] ),
            ( '_DataAdm_', [DATAADM, DATAVIEW] ),
            ( '_LogViewer_', [] ),
            ( '_MasterViewer_', [ SYSVIEW ] ),
            ( '_User_', [ USER ] ),
            ]

ek_initlist = [
    ( '@BASIC', 'Basic common keywords',
        [   ('', ''),
            ('X', 'undefined'),
        ]),

    ( '@ROLES', 'Group roles',
        [   (SYSADM, 'system administrator role'),
            (SYSVIEW, 'system viewer role'),
            (DATAADM, 'data administrator role'),
            (DATAVIEW, 'data viewer role'),
            (PUBLIC, 'public role - all visitor'),
            (USER, 'authenticated user role'),
            (GUEST, 'guest / anonymous user role'),
            (EK_CREATE, 'create new EnumKey (EK)'),
            (EK_MODIFY, 'modify EnumKey(EK)'),
            (EK_VIEW, 'view EnumKey(EK)'),
            (EK_DELETE, 'delete EnumKey (EK)'),
            (USERCLASS_CREATE, 'create new userclass'),
            (USERCLASS_MODIFY, 'modify userclass data'),
            (USERCLASS_VIEW, 'view userclass data'),
            (USERCLASS_DELETE, 'delete userclass data'),
            (USER_CREATE, 'create new user'),
            (USER_MODIFY, 'modify user data'),
            (USER_VIEW, 'view user data'),
            (USER_DELETE, 'delete user data'),
            (GROUP_CREATE, 'create new group'),
            (GROUP_MODIFY, 'modify group data'),
            (GROUP_VIEW, 'view group data'),
            (GROUP_DELETE, 'delete group data'),
            (GROUP_ADDUSER, 'add new user to group'),
            (GROUP_DELUSER, 'remove user from group')
        ]),

    ( '@ACTIONLOG', 'ActionLog',
        [   ('~user/add', ':: added new user %s'),
            ('~user/mod', ':: modified user %s'),
            ('~user/del', ':: deleted user %s'),
            ('~group/add', ':: added new group %s'),
            ('~group/mod', ':: modified group %s'),
            ('~group/del', ':: deleted group %s'),
            ('~group/adduser', ':: added to group %s user %s'),
            ('~group/deluser', ':: deleted from group %s user %s'),
            ('~ek/add', ':: added new EnumKey %s'),
            ('~ek/mod', ':: modified EnumKey %s'),
            ('~ek/del', ':: deleted EnumKey %s'),
            ('~userclass/add', ':: added new userclass %s'),
            ('~userclass/mod', ':: modified userclass %s'),
            ('~userclass/del', ':: deleted userclass %s')
        ]),

    ( '@FILETYPE', 'File type',
        [   ('file/file', ''),
            ('file/folder', ''),
            ('file/link', ''),
            ('file/content', ''),
        ]
    ),

    ( '@MIMETYPE', 'Mime type',
        [   ('application/x-directory', ''),
            ('application/x-url', ''),
            ('image/png', ''),
            ('image/jpeg', ''),
            ('image/gif', ''),
            ('image/svg+xml'),
            ('application/pdf', ''),
            ('application/postscript', ''),
            ('application/xml', ''),
            ('application/json', ''),
            ('application/octet-stream', ''),
            ('application/unknown', ''),
            ('text/plain', ''),
            ('text/html', ''),
            ('text/xml', ''),
            ('text/x-rst', 'mimetype reStructuredText'),         # reStructuredText
            ('text/x-markdown', 'mimeype MarkDown'),    # markdown
            ('text/x-mako', 'mimetype Mako template'),
        ]),
]


