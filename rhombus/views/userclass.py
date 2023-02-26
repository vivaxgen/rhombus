
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.roles import SYSADM
from rhombus.lib import tags as t
from rhombus.lib.tags import (div, table, thead, tbody, th, tr, td, literal, selection_bar, br, ul, li, a, i,
                              form, POST, GET, fieldset, input_text, input_hidden, input_select, input_password,
                              submit_bar, h2, h3, p, input_textarea)
from rhombus.views import (BaseViewer, render_to_response, form_submit_bar, ParseFormError, roles, yaml_load,
                           Response, HTTPFound, boolean_checkbox)
from rhombus.lib.modals import modal_delete, popup, modal_error

#from rhombus.views import *

import sqlalchemy.exc

import io, yaml


class UserClassViewer(BaseViewer):

    accessing_roles = [SYSADM]

    object_class = get_dbhandler().UserClass
    fetch_func = get_dbhandler().get_userclasses_by_ids
    edit_route = 'rhombus.userclass-edit'
    view_route = 'rhombus.userclass-view'

    form_fields = {
        'domain*': ('rhombus-userclass_domain', ),
        'desc': ('rhombus-userclass_desc', ),
        'autoadd': ('rhombus-userclass_autoadd', boolean_checkbox),
        'credscheme': ('rhombus-userclass_credscheme', yaml_load),
    }

    def index_helper(self):

        userclasses = self.dbh.get_userclasses()
        html, jscode = generate_userclass_table(userclasses, self.request)

        return render_to_response('rhombus:templates/generics/datatables_page.mako', {
            'title': 'Userclasses',
            'html': html,
            'code': jscode,
        }, request=self.request)

    def view_helper(self, render=True):

        userclass_html, userclass_jscode = super().view_helper(render=False)

        userclass_html.add(t.hr)

        user_html, user_js = generate_user_table(self.obj, self.request)
        userclass_html.add(user_html)
        userclass_jscode += user_js

        return self.render_edit_form(userclass_html, userclass_jscode)

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
                if 'collections.code' in detail or 'uq_collections_code' in detail:
                    raise ParseFormError(f'The collection code: {d["code"]}  is '
                                         f'already being used. Please use other collection code!',
                                         'messy-collection-code') from err

            raise RuntimeError(f'error updating object: {detail}')

        except sqlalchemy.exc.DataError as err:
            dbh.session().rollback()
            detail = err.args[0]

            raise RuntimeError(detail)

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        request = self.request
        ff = self.ffn

        eform = t.form(name='rhombus/userclass', method=POST, readonly=readonly,
                       update_dict=update_dict)
        eform.add(
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('domain*'), 'Domain', value=obj.domain, maxlength=16, required=True,
                             offset=2),
                t.input_text(ff('desc'), 'Description', value=obj.desc, maxlength=64,
                             offset=2),
                    t.checkboxes('rhombus-userclass_options', 'Options', [
                        (ff('autoadd'), 'Auto Add', obj.autoadd),
                    ], offset=2),
                t.input_textarea(ff('credscheme'), 'Cred Scheme', value=yaml.dump(obj.credscheme),
                                 offset=2),
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else div(),
                name='footer',
            ),
        )

        return t.div(t.h2('Userclass'), eform), ''

    def action_post(self):

        rq = self.request
        dbh = self.dbh
        _method = rq.POST.get('_method')

        if _method == 'delete':

            userclass_ids = [int(x) for x in rq.params.getall('userclass-ids')]
            userclasses = dbh.get_userclasses_by_ids(userclass_ids, groups=None, user=rq.identity)

            if len(userclasses) == 0:
                return Response(modal_error(content="Please select userclass to be removed!"))

            return Response(
                modal_delete(
                    title='Removing userclass(es)',
                    content=t.literal(
                        'You are going to remove the following userclass(es): '
                        '<ul>'
                        + ''.join(f'<li>{uc.domain}</li>' for uc in userclasses)
                        + '</ul>'
                    ), request=rq,

                ), request=rq
            )

        elif _method == 'delete/confirm':

            userclass_ids = [int(x) for x in rq.params.getall('userclass-ids')]
            userclasses = dbh.get_userclasses_by_ids(userclass_ids, groups=None, user=rq.identity)

            sess = dbh.session()
            count = left = 0
            for uc in userclasses:
                if uc.can_modify(rq.identity):
                    sess.delete(uc)
                    count += 1
                else:
                    left += 1

            sess.flush()
            rq.session.flash(
                ('success', f'You have successfully removed {count} userclass(es), '
                            f'kept {left} userclass(es).')
            )

            return HTTPFound(location=rq.referer)

        raise RuntimeError('No defined action')


def generate_userclass_table(userclasses, request):

    userclass_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('', style="width: 2em;"), th('UserClass / Domain'), th('Users')
        ],
        tbody()[
            tuple([tr()[
                td(literal('<input type="checkbox" name="userclass-ids" value="%d" />' % uc.id)),
                td('%s' % uc.domain),
                td(a('%d' % uc.users.count(), href=request.route_url('rhombus.userclass-view', id=uc.id)))
            ] for uc in userclasses])
        ]
    ]

    add_button = ('New userclass',
                  request.route_url('rhombus.userclass-add')
                  )

    bar = selection_bar('userclass-ids', action=request.route_url('rhombus.userclass-action'),
                        add=add_button)
    return bar.render(userclass_table)


def generate_user_table(userclass, request):

    user_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('Login'), th('Name'), th('Primary group')
        ],
        tbody()[
            tuple([tr()[
                td(a(u.login, href=request.route_url('rhombus.user-view', id=u.id))),
                td(u.fullname),
                td(a(u.primarygroup.name,
                     href=request.route_url('rhombus.group-view', id=u.primarygroup_id))),
            ] for u in userclass.users])
        ]
    ]

    add_button = ('New user',
                  request.route_url('rhombus.user-add', _query=dict(userclass_id=userclass.id))
                  )

    bar = selection_bar('user-ids', action=request.route_url('rhombus.user-action'),
                        add=add_button)
    return bar.render(user_table)


@roles(SYSADM)
def index(request):
    dbh = get_dbhandler()

    userclasses = dbh.get_userclass()
    userclass_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('', style="width: 2em;"), th('UserClass / Domain'), th('Users')
        ],
        tbody()[
            tuple([tr()[
                td(literal('<input type="checkbox" name="userclass-ids" value="%d" />' % uc.id)),
                td('%s' % uc.domain),
                td(a('%d' % uc.users.count(), href=request.route_url('rhombus.userclass-view', id=uc.id)))
            ] for uc in userclasses])
        ]
    ]

    add_button = ('New userclass',
                  request.route_url('rhombus.userclass-edit', id=0)
                  )

    bar = selection_bar('userclass-ids', action=request.route_url('rhombus.userclass-action'),
                        add=add_button)
    html, code = bar.render(userclass_table)

    return render_to_response(
        'rhombus:templates/generics/datatables_page.mako', {
            'title': 'Userclasses',
            'html': html,
            'code': code,
        }, request=request
    )


@roles(SYSADM)
def view(request):

    dbh = get_dbhandler()
    userclass = dbh.get_userclass(int(request.matchdict['id']))

    html = div(h3()[
        a('Userclass', href=request.route_url('rhombus.userclass')),
        f': {userclass.domain}',
    ])

    eform = edit_form(userclass, dbh, request, readonly=True)
    html.add(div(eform))

    user_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('Login'), th('Name'), th('Primary group')
        ],
        tbody()[
            tuple([tr()[
                td(a(u.login, href=request.route_url('rhombus.user-view', id=u.id))),
                td(u.fullname),
                td(a(u.primarygroup.name,
                     href=request.route_url('rhombus.group-view', id=u.primarygroup_id))),
            ] for u in userclass.users])
        ]
    ]

    html.add(user_table)

    return render_to_response('rhombus:templates/generics/page.mako',
                              {'html': html},
                              request=request)


@roles(SYSADM)
def edit(request):

    userclass_id = int(request.matchdict['id'])
    if userclass_id < 0:
        return error_page(request, 'Please provide userclass ID')

    dbh = get_dbhandler()

    if request.method == 'GET':

        if userclass_id == 0:
            userclass = dbh.UserClass()
            userclass.id = 0

        else:
            userclass = dbh.get_userclass(userclass_id)

        html = div(h3('Edit Userclass'))
        editform = edit_form(userclass, dbh, request)
        html.add(editform)

        return render_to_response("rhombus:templates/generics/page.mako",
                                  {'html': html,
                                   }, request=request)

    elif request.POST:

        userclass_d = parse_form( request.POST )
        if userclass_d['id'] != userclass_id:
            return error_page(request, "Inconsistent data!")

        try:
            if userclass_id == 0:
                userclass = dbh.UserClass()
                userclass.update( userclass_d )
                dbh.session().add( userclass )
                dbh.session().flush()
                request.session.flash(
                    (   'success',
                        'Userclass [%s] has been created.' % userclass.domain )
                )

            else:
                userclass = dbh.get_userclass(userclass_id)
                userclass.update( userclass_d )
                dbh.session().flush()

        except RuntimeError as err:
            return error_page(request, str(err))

        except:
            raise

        return HTTPFound(location = request.route_url('rhombus.userclass-view', id=userclass.id))

    raise NotImplementedError()


def getusers(request):
    pass


def action(request):
    raise NotImplementedError()


def edit_form(userclass, dbh, request, readonly=False):

    eform = form(name='rhombus/userclass', method=POST, readonly=readonly,
                 action=request.route_url('rhombus.userclass-edit', id=userclass.id))
    eform.add(
        fieldset(
            input_hidden(name='rhombus-userclass_id', value=userclass.id),
            input_text('rhombus-userclass_domain', 'Domain', value=userclass.domain),
            input_text('rhombus-userclass_desc', 'Description', value=userclass.desc),
            input_textarea('rhombus-userclass_credscheme', 'Cred Scheme', value=yaml.dump(userclass.credscheme)),
            submit_bar() if not readonly else a('Edit', class_='btn btn-primary offset-md-3',
                                                href=request.route_url('rhombus.userclass-edit',
                                                                       id=userclass.id)),
        )
    )

    return eform


def parse_form( f ):

    d = dict()
    d['id'] = int(f['rhombus-userclass_id'])
    d['domain'] = f['rhombus-userclass_domain']
    d['desc'] = f['rhombus-userclass_desc']
    d['credscheme'] = yaml.load(io.StringIO(f['rhombus-userclass_credscheme']), Loader=yaml.CLoader)

    return d

# in-memory data

_SYNCTOKENS_ = []   # [ (token, create_time), ...]


def get_token():
    pass

def validate_token( token ):
    pass
