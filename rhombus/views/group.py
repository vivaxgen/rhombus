
from rhombus.views import *

from rhombus.models.user import Group

import json


@roles( PUBLIC )
def index(request):
    """ list groups """

    dbh = get_dbhandler()
    groups = Group.query(dbh.session())

    html, code = format_grouptable(groups, request)

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

    return render_to_response("rhombus:templates/group/view.mako",
        {   'group': group,
            'form': grp_form,
        }, request = request)


def edit(request):
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


def format_grouptable(groups, request):
    """ return (html, code)
    """

    T = table(class_='table table-condensed table-striped', id='grouptable')

    data = [
        [   ' ',
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
