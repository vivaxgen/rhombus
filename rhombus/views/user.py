
from rhombus.lib.utils import get_dbhandler
from rhombus.views import *
from rhombus.views.generics import error_page

@roles(SYSADM)
def index(request):

    dbh = get_dbhandler()

    users = dbh.get_user()
    user_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('', style='width: 2em'), th('Username'), th('Userclass/Domain')
        ],
        tbody()[
            tuple(
                [ tr()
                    [   td(),
                        td(a('%s' % u.login, href=request.route_url('rhombus.user-view', id=u.id))),
                        td('%s' % u.userclass.domain)
                    ]   for u in users
                ]
            )
        ]
    ]

    add_button = ( 'New user',
                    request.route_url('rhombus.user-edit', id=0)
    )

    bar = selection_bar('user-ids', action=request.route_url('rhombus.user-action'),
                    add = add_button)
    html, code = bar.render(user_table)

    return render_to_response('rhombus:templates/generics/page.mako',
            {   'html': html,
                'code': code
            }, request = request )


@roles(SYSADM)
def view(request):

    dbh = get_dbhandler()
    user = dbh.get_user( int(request.matchdict['id']) )

    html = div( div(h3('User View')) )

    eform = edit_form(user, dbh, request, static=True)
    html.add( eform )

    return render_to_response('rhombus:templates/generics/page.mako',
        {   'html': html,
        }, request = request )


@roles(SYSADM)
def edit(request):

    user_id = int(request.matchdict['id'])
    if user_id < 0:
        return error_page(request, 'Please provide userclass ID')

    dbh = get_dbhandler()

    if request.method == 'GET':

        if user_id == 0:
            user = dbh.User()
            user.id = 0

        else:
            user = dbh.get_user(user_id)

        editform = edit_form(user, dbh, request)

        return render_to_response( "rhombus:templates/generics/page.mako",
                {   'html': editform,
                }, request = request
        )

    elif request.POST:

        user_d = parse_form( request.POST )
        if user_d['id'] != user_id:
            return error_page(request, "Inconsistent data!")

        try:
            if user_id == 0:
                # create a new user

                userclass = dbh.get_userclass( user_d['userclass_id'])
                user = userclass.add_user(
                    login = user_d['login'],
                    lastname = user_d['lastname'],
                    firstname = user_d['firstname'],
                    email = user_d['email'],
                    primarygroup = user_d['primarygroup_id'],

                )
                user.institution = user_d['institution']
                dbh.session().flush()
                request.session.flash(
                    (   'success',
                        'User [%s] has been created.' % user.login )
                )

            else:
                user = dbh.get_user(user_id)
                user.update( user_d )
                dbh.session().flush()

        except RuntimeError as err:
            return error_page(request, str(err))

        except:
            raise

        return HTTPFound(location = request.route_url('rhombus.user-view', id=user.id))

    raise NotImplementedError()


def edit_form(user, dbh, request, static=False):

    eform = form( name='rhombus/user', method=POST,
                action=request.route_url('rhombus.user-edit', id=user.id))
    eform.add(
        fieldset(
            input_hidden(name='rhombus-user_id', value=user.id),
            input_select('rhombus-user_userclass_id', 'User class', value=user.userclass_id,
                static=static, options = [ (uc.id, uc.domain) for uc in dbh.get_userclass() ]),
            input_text('rhombus-user_login', 'Login', value=user.login,
                static=static),
            input_text('rhombus-user_lastname', 'Lastname', value=user.lastname,
                static=static),
            input_text('rhombus-user_firstname', 'Firstname', value=user.firstname,
                static=static),
            input_text('rhombus-user_email', 'E-mail', value=user.email,
                static=static),
            input_select('rhombus-user_primarygroup_id', 'Primary group', value=user.primarygroup_id,
                static=static, options = [ (g.id, g.name) for g in dbh.get_group() ]),
            input_text('rhombus-user_institution', 'Institution', value=user.institution,
                    static=static),
            submit_bar() if not static else a('Edit', class_='btn btn-primary col-md-offset-3',
                            href=request.route_url('rhombus.user-edit', id=user.id)),
        )
    )

    return eform


def parse_form( f ):

    d = dict()
    d['id'] = int(f['rhombus-user_id'])
    d['userclass_id'] = int(f['rhombus-user_userclass_id'])
    d['login'] = f['rhombus-user_login']
    d['lastname'] = f['rhombus-user_lastname']
    d['firstname'] = f['rhombus-user_firstname']
    d['email'] = f['rhombus-user_email']
    d['primarygroup_id'] = int(f['rhombus-user_primarygroup_id'])
    d['institution'] = f['rhombus-user_institution']
    return d


@roles(PUBLIC)
def passwd(request):

    #user_id = int(request.matchdict.get('id', -1))
    dbh = get_dbhandler()
    #user = dbh.get_user(user_id)

    #if request.user.id != user_id and not request.user.has_roles(SYSADM):
    #    return error_page(request,
    #        'ERR: except system administrator, user can only change his/her own password')

    #if user.credential == '{X}':
    #    return error_page(request,
    #        'ERR: user is using external authentication scheme!')

    if request.POST:

        user = request.user
        eform = password_form(user)

        if user.has_roles(SYSADM):
            # set up variables
            login = request.POST.get('username')
            current_user = dbh.get_user(user.id)
            target_user = dbh.get_user(login)
            eform.get('username').value = login

            if not target_user:
                eform.get('username').add_error('User does not exist!')
                return render_to_response('rhombus:templates/generics/page.mako',
                        { 'content': str(eform) },
                        request = request )

        else:
            target_user = dbh.get_user(int(request.POST.get('user_id', -1)))
            if target_user.id != user.id:
                raise RuntimeError('ERR: users can only change their own passwords!')
            current_user = target_user

        curr_pass = request.POST.get('curr_pass', None)

        if current_user.verify_credential(curr_pass):
            new_pass = request.POST.get('new_pass', None)
            if new_pass:
                if new_pass == request.POST.get('new_pass2', None):
                    target_user.set_credential(new_pass)
                    # reset eform
                    eform=None
                else:
                    eform.get('new_pass2').add_error('Password is not verified!')
            else:
                eform.get('new_pass').add_error('Please fill the new password!')
        else:
            eform.get('curr_pass').add_error('Incorrect password!')

        if eform:
            return render_to_response('rhombus:templates/generics/page.mako',
                { 'content': str(eform) },
                request = request )

        request.session.flash( ('success',
            'Successfully changed password for user %s' % target_user.login) )
        return HTTPFound(location = request.referer or '/')

    eform = password_form(request.user)

    return render_to_response('rhombus:templates/generics/page.mako',
            { 'content': str(eform) },
            request = request )


def password_form(user):

    eform = form('rhombus.password', method='POST')
    eform.add(
        fieldset()[
            input_hidden('user_id', value = user.id),
            input_show('login', 'Login', value = user.login),
            input_password('curr_pass', 'Current password'),
        ],
        fieldset()[
            input_text('username', 'Username', value = user.login)
                if user.has_roles(SYSADM) else '',
            input_password('new_pass', 'New password'),
            input_password('new_pass2', 'Verify password')
        ],
        fieldset()[
            submit_bar('Change password')]
    )

    return eform


def action(request):
    pass


def user_menu(request):
    """ return a HTML for user menu, bootstrap-based """
    user_menu_html = ul(class_ = 'nav navbar-nav navbar-right')
    if request.user:
        user_menu_list = li(class_ = "active dropdown" )[
                a(class_='dropdown-toggle', role='button',
                    **  { 'data-toggle': 'dropdown',
                            'aria-haspopup': 'true',
                            'aria-expanded': 'false',
                        }
                )[
                    span(class_='fa fa-user'),
                    ' ' + request.user.login + ' ',
                    span(class_='caret')
                ],
                ul(class_='dropdown-menu')[
                    li(a('Change password',
                            href=request.route_url('rhombus.user-passwd')))
                        if not request.user.has_roles(GUEST) else '',
                    li(a('Management', href=request.route_url('rhombus.dashboard')))
                        if request.user.has_roles(SYSADM) else '',
                    li(a('Logout', href='/logout'))
                ]

            ]
    else:
        user_menu_list = li(class_ = 'active dropdown')[
                a(href='/login')[
                    span(class_='fa fa-sign-in'),
                    ' Login '
                ]
            ]
    user_menu_html.add( user_menu_list )

    return user_menu_html
