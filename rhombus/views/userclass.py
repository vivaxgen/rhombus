
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.roles import SYSADM
from rhombus.lib.tags import (div, table, thead, tbody, th, tr, td, literal, selection_bar, br, ul, li, a, i,
                              form, POST, GET, fieldset, input_text, input_hidden, input_select, input_password,
                              submit_bar, h3, p, input_textarea)
from rhombus.views import *

import io, yaml

@roles(SYSADM)
def index(request):
    dbh = get_dbhandler()

    userclasses = dbh.get_userclass()
    userclass_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('', style="width: 2em;"), th('UserClass / Domain'), th('Users')
        ],
        tbody()[
            tuple([ tr()[
                        td(literal('<input type="checkbox" name="userclass-ids" value="%d" />' % uc.id)),
                        td('%s' % uc.domain),
                        td(a('%d' % uc.users.count(), href=request.route_url('rhombus.userclass-view', id=uc.id)) )
                    ] for uc in userclasses ])
        ]
    ]

    add_button = ( 'New userclass',
                    request.route_url('rhombus.userclass-edit', id=0)
    )

    bar = selection_bar('userclass-ids', action=request.route_url('rhombus.userclass-action'),
                    add = add_button)
    html, code = bar.render(userclass_table)

    return render_to_response('rhombus:templates/generics/page.mako',
            {   'html': html,
                'code': code },
            request = request )


@roles(SYSADM)
def view(request):

    dbh = get_dbhandler()
    userclass = dbh.get_userclass( int(request.matchdict['id']) )

    html = div( div(h3('Userclass: %s' % userclass.domain)))

    eform = edit_form(userclass, dbh, request, static=True)
    html.add( div(eform) )

    user_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('Login'), th('Name'), th('Primary group')
        ],
        tbody()[
            tuple([ tr()[
                        td(a(u.login, href=request.route_url('rhombus.user-view', id=u.id))),
                        td(u.fullname),
                        td(a(u.primarygroup.name,
                            href=request.route_url('rhombus.group-view', id=u.primarygroup_id))),
                    ] for u in userclass.users ])
        ]
    ]

    html.add(user_table)

    return render_to_response('rhombus:templates/generics/page.mako',
            { 'content': str(html) },
            request = request )


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

        editform = edit_form(userclass, dbh, request)

        return render_to_response( "rhombus:templates/generics/page.mako",
                {   'html': editform,
                }, request = request
        )

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


def edit_form(userclass, dbh, request, static=False):

    eform = form( name='rhombus/userclass', method=POST,
                action=request.route_url('rhombus.userclass-edit', id=userclass.id))
    eform.add(
        fieldset(
            input_hidden(name='rhombus-userclass_id', value=userclass.id),
            input_text('rhombus-userclass_domain', 'Domain', value=userclass.domain,
                static=static),
            input_text('rhombus-userclass_desc', 'Description', value=userclass.desc,
                static=static),
            input_textarea('rhombus-userclass_credscheme', 'Cred Scheme', value=yaml.dump(userclass.credscheme),
                    static=static),
            submit_bar() if not static else a('Edit', class_='btn btn-primary col-md-offset-3',
                            href=request.route_url('rhombus.userclass-edit', id=userclass.id)),
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
