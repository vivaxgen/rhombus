
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.roles import PUBLIC, SYSADM, GUEST, EK_VIEW, USERCLASS_VIEW, USER_VIEW, GROUP_VIEW
from rhombus.lib.modals import popup, modal_delete
from rhombus.lib.tags import (div, table, thead, tbody, th, tr, td, literal, selection_bar, br, ul, li, a, i,
                              form, POST, GET, fieldset, input_text, input_hidden, input_select, input_password,
                              submit_bar, hr, h3, h5, p, custom_submit_bar)
from rhombus.lib import tags as t
from rhombus.lib.modals import modal_delete, popup, modal_error
from rhombus.views import (BaseViewer, render_to_response, form_submit_bar, ParseFormError,
                           roles, yaml_load, Response, HTTPFound, m_roles, get_login_url,
                           get_logout_url)
from rhombus.views import *
from rhombus.views.generics import error_page

import sqlalchemy.exc
from sqlalchemy import or_

import urllib.parse


class UserViewer(BaseViewer):

    accessing_roles = BaseViewer.accessing_roles

    object_class = get_dbhandler().User
    fetch_func = get_dbhandler().get_users_by_ids
    edit_route = 'rhombus.user-edit'
    view_route = 'rhombus.user-view'

    form_fields = {
        'login!': ('rhombus-user-login', ),
        'userclass_id': ('rhombus-user-userclass_id', int),
        'lastname': ('rhombus-user-lastname', ),
        'firstname': ('rhombus-user-firstname', ),
        'email!': ('rhombus-user-email', ),
        'email2': ('rhombus-user-email2', ),
        'primarygroup_id': ('rhombus-user-primarygroup_id', int),
        'institution': ('rhombus-user-institution', ),
    }

    def index_helper(self):

        users = self.dbh.get_users()
        html, jscode = generate_user_table(users, self.request)

        return render_to_response('rhombus:templates/generics/datatables_page.mako', {
            'title': 'Users',
            'html': html,
            'code': jscode,
        }, request=self.request)

    def view_extender(self, html, jscode):

        user = self.obj

        html, jscode = super().view_extender(html, jscode)

        html.add(t.br, t.p('Groups: %s' % ' | '.join([g.name for g in user.groups or []])))

        html.add(t.div(t.hr, t.h3('Token Generator', styles="bg-dark;")))
        tokenform = t.form(name='rhombus/token-generator', method=POST,
                           action=self.request.route_url('rhombus.user-action'))
        tokenform.add(
            custom_submit_bar(('Generate token', 'generate_token')).set_offset(1).show_reset_button(False)
        )
        html.add(tokenform)

        return html, jscode

    def update_object(self, obj, d):

        dbh = self.dbh

        try:
            obj.update(d)
            if obj.id is None:
                dbh.session().add(obj)
            dbh.session().flush([obj])

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            if 'UNIQUE' in detail or 'UniqueViolation' in detail:
                if 'users.login' in detail or 'uq_users_login' in detail:
                    raise ParseFormError(f'The login username: {d["login"]} is '
                                         f'already being used. Please use other username!',
                                         self.ffn('login!')) from err
                elif 'users.email' in detail or 'uq_users_email' in detail:
                    raise ParseFormError(f'The email address: {d["email"]} has '
                                         f'already being used.',
                                         self.ffn('email!')) from err

            raise RuntimeError(f'error updating object: {detail}')

        except sqlalchemy.exc.DataError as err:
            dbh.session().rollback()
            detail = err.args[0]

            raise RuntimeError(detail)

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        user = obj or self.obj
        dbh = self.dbh
        request = self.request
        ff = self.ffn

        eform = t.form(name='rhombus/user', method=POST, readonly=readonly,
                       update_dict=update_dict)
        eform.add(
            self.hidden_fields(obj),
            t.fieldset(
                t.input_select(ff('userclass_id'), 'User class', value=user.userclass_id,
                               offset=2,
                               options=[(uc.id, uc.domain) for uc in dbh.get_userclass()]),
                t.input_text(ff('login!'), 'Login', value=user.login, offset=2, maxlength=16, required=True),
                t.input_text(ff('lastname'), 'Lastname', value=user.lastname, offset=2),
                t.input_text(ff('firstname'), 'Firstname', value=user.firstname, offset=2),
                t.input_text(ff('email!'), 'Primary email', value=user.email, offset=2, required=True),
                t.input_text(ff('email2'), 'Secondary email', value=user.email2, offset=2),
                t.input_select(
                    ff('primarygroup_id'), 'Primary group', value=user.primarygroup_id, offset=2,
                    options=[
                        (g.id, g.name)
                        for g in dbh.get_group(
                            systemgroups=True if (readonly or request.user.has_roles(SYSADM)) else False)
                    ]
                ),
                t.input_text(ff('institution'), 'Institution', value=user.institution, offset=2),
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else div(),
                #submit_bar() if not readonly else t.a('Edit',
                #                                      class_='btn btn-primary offset-md-3',
                #                                      href=request.route_url('rhombus.user-edit',
                #                                                             id=user.id)),
                name='footer',
            )
        )

        return t.div()[t.h2('User'), eform], ''

    def lookup_helper(self):
        """ return JSON for autocomplete """
        q = self.request.params.get('q')

        if not q:
            return error_page(self.request)

        q = '%' + q.lower() + '%'

        dbh = self.dbh
        users = dbh.User.query(dbh.session()).filter(or_(dbh.User.login.ilike(q),
                                                         dbh.User.lastname.ilike(q),
                                                         dbh.User.firstname.ilike(q)))

        # formating for select2 consumption

        result = [
            {'id': u.id, 'text': u.render()}
            for u in users]

        return result

    def action_post(self):

        request = self.request
        dbh = self.dbh
        method = request.params.get('_method', None)
        dbh = get_dbhandler()

        if method == 'delete':

            user_ids = [int(x) for x in request.params.getall('user-ids')]
            users = dbh.get_user(user_ids)

            if len(users) == 0:
                return Response(
                    modal_error(
                        content=literal('Please select user(s) to be removed'),
                    )
                )

            #return Response( modal_delete %
            #    ''.join( '<li>%s | %s, %s | %s</li>' %
            #        (u.login, u.lastname, u.firstname, u.userclass.domain) for u in users))
            return Response(
                modal_delete(
                    title='Deleting User(s)',
                    content=literal(
                        'You are going to delete the following user(s):'
                        '<ul>' +
                        ''.join('<li>%s | %s, %s | %s</li>' % (u.login, u.lastname,
                                u.firstname, u.userclass.domain) for u in users) +
                        '</ul>'
                    ),
                    request=request
                ),
                request=request
            )

        elif method == 'delete/confirm':

            user_ids = [int(x) for x in request.params.getall('user-ids')]
            logins = []
            for user in dbh.get_user(user_ids):
                logins.append(user.login)
                dbh.session().delete(user)

            dbh.session().flush()
            request.session.flash(
                ('success', 'User %s has been deleted successfully' % ','.join(logins)))

            return HTTPFound(location=request.referrer or request.route_url('rhombus.user'))

        elif method == 'generate_token':

            from rhombus.lib.rpc import generate_user_token

            token = generate_user_token(request)
            html = div(h3('User Token'), div('Please save your token in secure location:'), h5(token))

            return render_to_response('rhombus:templates/generics/page.mako',
                                      {'html': html},
                                      request=request)

        raise RuntimeError('FATAL - programming ERROR')

    @m_roles(PUBLIC)
    def passwd(self):
        request = self.request

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
                                              {'html': eform},
                                              request=request
                                              )

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
                        eform = None
                    else:
                        eform.get('new_pass2').add_error('Password is not verified!')
                else:
                    eform.get('new_pass').add_error('Please fill the new password!')
            else:
                eform.get('curr_pass').add_error('Incorrect password!')

            if eform:
                raise
                return render_to_response('rhombus:templates/generics/page.mako',
                                          {'html': eform},
                                          request=request
                                          )

            request.session.flash((
                'success',
                'Successfully changed password for user %s' % target_user.login)
            )
            return HTTPFound(location=request.referer or '/')

        eform = password_form(request.user)

        return render_to_response('rhombus:templates/generics/page.mako',
                                  {'html': eform},
                                  request=request,
                                  )


def generate_user_table(users, request):

    user_table = t.table(class_='table table-condensed table-striped')[
        t.thead()[
            t.th('', style='width: 2em'), th('Username'), th('Userclass/Domain')
        ],
        t.tbody()[
            tuple([
                t.tr()[
                    t.td(literal('<input type="checkbox" name="user-ids" value="%d">' % u.id)),
                    t.td(a('%s' % u.login, href=request.route_url('rhombus.user-view', id=u.id))),
                    t.td('%s' % u.userclass.domain)
                ] for u in users
            ])
        ]
    ]

    add_button = (
        'New user',
        request.route_url('rhombus.user-add')
    )

    bar = t.selection_bar(
        'user-ids', action=request.route_url('rhombus.user-action'),
        add=add_button
    )

    return bar.render(user_table)


def password_form(user):

    eform = form('rhombus.password', method='POST')
    eform.add(
        fieldset()[
            input_hidden(name='user_id', value=user.id),
            input_text('login', 'Login', value=user.login, readonly=True),
            input_password('curr_pass', 'Current password'),
        ],
        fieldset()[
            input_text('username', 'Username', value=user.login)
            if user.has_roles(SYSADM) else '',
            input_password('new_pass', 'New password'),
            input_password('new_pass2', 'Verify password')
        ],
        fieldset()[
            submit_bar('Change password')]
    )

    return eform


def user_menu(request):
    """ return a HTML for user menu, bootstrap-based """
    authhost = request.registry.settings.get('rhombus.authhost', '')
    # url_login = authhost + '/login?'
    # url_logout = authhost + '/logout?'
    user_menu_html = ul(class_='navbar-nav me-auto navbar-nav-scroll')
    if request.user:
        user_menu_list = li(class_="nav-item active dropdown")[
            a(class_='nav-link dropdown-toggle', id="navbarUsermenu",
              ** {'data-bs-toggle': 'dropdown',
                  'role': 'button',
                  'aria-expanded': 'false',
                  }
              )[
                i(class_='fas fa-user-circle'),
                ' ' + request.user.login,
            ],
            ul(class_='dropdown-menu dropdown-menu-end', ** {'aria-labelledby': 'navbarUsermenu'})[
                li(a('Profile', class_='dropdown-item',
                     href=request.route_url('rhombus.user-view', id=request.user.id)))
                if not request.user.has_roles(GUEST) else '',
                li(a('Change password', class_='dropdown-item',
                     href=request.route_url('rhombus.user-passwd')))
                if not (request.user.has_roles(GUEST) or authhost) else '',
                li(a('Management', class_='dropdown-item',
                     href=request.route_url('rhombus.dashboard')))
                if request.user.has_roles(SYSADM, SYSVIEW, DATAADM, DATAVIEW,
                                          EK_VIEW, USERCLASS_VIEW, USER_VIEW, GROUP_VIEW) else '',
                li(a('Logout', class_='dropdown-item', href=get_logout_url(request, authhost)))
            ]
        ]

    else:
        user_menu_list = li(class_='nav-item active')[
            a(class_='nav-link',
              href=get_login_url(request, authhost))[
                i(class_='fas fa-sign-in-alt'),
                ' Login '
            ]
        ]
    user_menu_html.add(user_menu_list)

    return user_menu_html

# EOF
