
from rhombus.views import *

from rhombus.models.user import Group

import json


@roles( PUBLIC )
def index(request):
    """ list groups """

    dbh = get_dbhandler()
    groups = Group.query(dbh.session())

    html, code = format_grouptable(groups, request)

    if request.user.has_roles(SYSADM):

        add_button = ( 'New group',
                        request.route_url('rhombus.group-edit', id=0)
        )

        bar = selection_bar('group-ids', action=request.route_url('rhombus.group-action'),
                    add = add_button)
        html, code = bar.render(html, code)


    return render_to_response('rhombus:templates/group/index.mako',
                {   'html': html,
                    'code': code,
                }, request=request )


@roles( PUBLIC )
def view(request):

    dbh = get_dbhandler()
    grp_id = int(request.matchdict.get('id'))
    group = dbh.get_group_by_id(grp_id)

    grp_form = edit_form(group, dbh, request, static=True)

    role_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('', style="width: 5px;"), th('Roles'), th('Description')
        ],
        tbody()[
            tuple([
                tr()[
                    td(literal('<input type="checkbox" name="role-ids" value="%d"/>' % r.id)),
                    td(r.key),
                    td(r.desc)
                ] for r in group.roles
            ])
        ]
    ]
    role_bar = selection_bar('role-ids', action=request.route_url('rhombus.group-action'))
    role_table, role_js = role_bar.render(role_table)

    user_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('', style="width: 5px;"), th('Login'), th('Name'), th('Primary group')
        ],
        tbody()[
            tuple([ tr()[
                        td(literal('<input type="checkbox" name="user-ids" value="%d" />' % u.id)),
                        td(a(u.login, href=request.route_url('rhombus.user-view', id=u.id))),
                        td(u.fullname()),
                        td(a(u.primarygroup.name,
                            href=request.route_url('rhombus.group-view', id=u.primarygroup_id))),
                    ] for u in group.users ])
        ]
    ]
    user_bar = selection_bar('user-ids', action=request.route_url('rhombus.group-action'))
    user_table, user_js = user_bar.render(user_table)

    return render_to_response("rhombus:templates/group/view.mako",
        {   'group': group,
            'form': grp_form,
            'role_table': role_table,
            'user_table': user_table,
            'code': role_js + user_js
        }, request = request)


@roles( SYSADM )
def edit(request):

    grp_id = int(request.matchdict['id'])
    if grp_id < 0:
        return error_page(request, 'Please provide group ID')

    dbh = get_dbhandler()

    if request.method == 'GET':

        if grp_id == 0:
            group = dbh.Group()
            group.id = 0

        else:
            group = dbh.get_group(grp_id)

        editform = edit_form(group, dbh, request)

        return render_to_response( "rhombus:templates/generics/page.mako",
                {   'content': str(editform),
                }, request = request
        )

    elif request.POST:

        group_d = parse_form( request.POST )
        if group_d['id'] != grp_id:
            return error_page(request, "Inconsistent data!")

        try:
            if grp_id == 0:
                group = dbh.Group()
                group.update( group_d )
                dbh.session().add( group )
                dbh.session().flush()
                request.session.flash(
                    (   'success',
                        'Group [%s] has been created.' % group.name )
                )

            else:
                group = dbh.get_group(grp_id)

                #check security here

                group.update( group_d )
                dbh.session().flush()

        except RuntimeError as err:
            return error_page(request, str(err))

        except:
            raise

        return HTTPFound(location = request.route_url('rhombus.group-view', id=group.id))

    raise NotImplementedError


def save(request):
    raise NotImplementedError


def action(requst):
    raise NotImplementedError


def lookup(request):
    raise NotImplementedError


def edit_form(group, dbh, request, static=False):

    eform = form( name='rhombus/group', method=POST,
                action=request.route_url('rhombus.group-edit', id=group.id))
    eform.add(
        fieldset(
            input_hidden(name='rhombus-group_id', value=group.id),
            input_text('rhombus-group_name', 'Group Name', value=group.name,
                static=static),
            input_text('rhombus-group_desc', 'Description', value=group.desc,
                static=static),
            input_textarea('rhombus-group_scheme', 'Scheme', value=group.scheme,
                    static=static),
            submit_bar() if not static else a('Edit', class_='btn btn-primary',
                            href=request.route_url('rhombus.group-edit', id=group.id)),
        )
    )

    return eform


def parse_form( f ):

    d = dict()
    d['id'] = int(f['rhombus-group_id'])
    d['name'] = f['rhombus-group_name']
    d['desc'] = f['rhombus-group_desc']
    d['scheme'] = f['rhombus-group_scheme']

    return d


def format_grouptable(groups, request):
    """ return (html, code)
    """

    T = table(class_='table table-condensed table-striped', id='grouptable')

    data = [
        [   '<input type="checkbox" name="group-ids" value="%d" />' % g.id,
            '<a href="%s">%s</a>' %
                (request.route_url('rhombus.group-view', id=g.id), g.name),
            len(g.users)
        ] for g in groups
    ]

    jscode = '''
var dataset = %s;

$(document).ready(function() {
    $('#grouptable').DataTable( {
        data: dataset,
        paging: false,
        fixedHeader: true,
        order: [ [1, "asc"] ],
        columns: [
            { title: " ", "orderable": false, "width": "15px" },
            { title: "Group Name" },
            { title: "Members", "orderable": false }
        ]
    } );
} );
''' % json.dumps( data )

    return (T, jscode)
