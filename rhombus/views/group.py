
from rhombus.views import *
from rhombus.views.generics import error_page
from rhombus.lib.tags import button
from rhombus.lib.roles import (PUBLIC, SYSADM, SYSVIEW, GROUP_CREATE, GROUP_MODIFY, GROUP_DELETE,
                               GROUP_ADDUSER, GROUP_DELUSER, EK_VIEW)
from rhombus.lib.tags import (div, table, thead, tbody, th, tr, td, literal, selection_bar, br, ul,
                              li, a, i, form, fieldset, input_hidden, input_text, input_select, 
                              input_textarea, checkboxes, submit_bar, POST, GET)
from rhombus.lib.modals import popup, modal_delete
from rhombus.models.user import Group

from pyramid.renderers import render

from sqlalchemy import exc

import json


@roles( PUBLIC )
def index(request):
    """ list groups """

    dbh = get_dbhandler()
    groups = Group.query(dbh.session())

    html, code = format_grouptable(groups, request)

    if request.user.has_roles(SYSADM, GROUP_CREATE):

        add_button = ('New group',
                      request.route_url('rhombus.group-edit', id=0)
                      )

        bar = selection_bar('group-ids', action=request.route_url('rhombus.group-action'),
                            add=add_button)
        html, code = bar.render(html, code)

    return render_to_response(
        'rhombus:templates/generics/datatables_page.mako', {
            'title': 'Groups',
            'html': html,
            'code': code,
        }, request=request
    )


@roles( PUBLIC )
def view(request):

    dbh = get_dbhandler()
    grp_id = int(request.matchdict.get('id'))
    group = dbh.get_group_by_id(grp_id)

    grp_form, grp_js = edit_form(group, dbh, request, readonly=True)

    if request.user.has_roles(SYSADM, GROUP_CREATE, GROUP_MODIFY, GROUP_DELETE):
        role_table, role_js = format_roletable(group, request)
    else:
        role_table, role_js = '', ''

    if request.user.has_roles(SYSADM, GROUP_CREATE, GROUP_DELETE, GROUP_ADDUSER,
            GROUP_DELUSER):
        user_table, user_js = format_usertable(group, request)
    else:
        user_table, user_js = '', ''

    return render_to_response("rhombus:templates/group/view.mako",
        {   'group': group,
            'form': grp_form,
            'role_table': role_table,
            'user_table': user_table,
            'code': role_js + user_js
        }, request = request)


@roles( SYSADM, GROUP_MODIFY )
def edit(request):

    grp_id = int(request.matchdict['id'])
    if grp_id < 0:
        return error_page(request, 'Please provide group ID')

    dbh = get_dbhandler()

    if request.method == 'GET':

        if grp_id == 0:
            group = dbh.Group(flags=0)
            group.id = 0

        else:
            group = dbh.get_group(grp_id)

        editform, editjs = edit_form(group, dbh, request)

        return render_to_response( "rhombus:templates/generics/formpage.mako",
                {   'html': editform,
                    'code': editjs,
                }, request = request
        )

    elif request.POST:

        group_d = parse_form( request.POST )
        if group_d['id'] != grp_id:
            return error_page(request, "Inconsistent data!")

        try:
            if grp_id == 0:
                group = dbh.Group(flags=0)
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


@roles(SYSADM, GROUP_DELETE)
def action(request):

    if request.POST:
        return action_post(request)
    return action_get(request)


def action_get(request):
    raise NotImplementedError()


def action_post(request):

    method = request.params.get('_method', None)
    dbh = get_dbhandler()

    if method == 'delete':

        group_ids = [ int(x) for x in request.params.getall('group-ids') ]
        groups = dbh.get_group( group_ids )

        if len(groups) == 0:
            return Response(modal_error)

        return Response(
            modal_delete(
                title = 'Deleting Group(s)',
                content = literal(
                    'You are going to delete the following group(s):'
                    '<ul>' +
                    ''.join( '<li>%s | %s</li>' % (g.name, len(g.users))
                                        for g in groups ) +
                    '</ul>'
                ),
                request = request
            ),
            request = request
        )

    elif method == 'delete/confirm':

        group_ids = [ int(x) for x in request.params.getall('group-ids') ]
        group_names = []
        for group in dbh.get_group( group_ids ):
            # XXX: check whether there are users with this group as primary group
            n_users =  dbh.User.query(dbh.session()).filter(dbh.User.primarygroup_id == group.id).count()
            if n_users > 0:
                return error_page( request,
                    'Group %s cannot be deleted since it currently is a primary group with %d user member(s).'
                        % (group.name, n_users) )
            group_names.append( group.name )
            dbh.session().delete(group)

        dbh.session().flush()
        request.session.flash(
            ('success', 'Group %s has been deleted successfully' % ','.join( group_names )))

        return HTTPFound( location = request.referrer or request.route_url( 'rhombus.group'))

    raise RuntimeError('FATAL - programming ERROR')


@roles(SYSADM, GROUP_CREATE, GROUP_MODIFY, GROUP_ADDUSER, GROUP_DELUSER)
def user_action(request):

    method = request.params.get('_method', None)
    dbh = get_dbhandler()

    if request.POST and method == 'add-member':

        useradd_id = int(request.params.get('useradd_id'))
        group_id = int(request.params.get('group_id'))
        role = request.params.get('useradd_role').upper()

        user = dbh.get_user(useradd_id)
        group = dbh.get_group(group_id)
        user_login = user.login
        group_name = group.name

        try:
            ug = dbh.UserGroup(user, group, role)
            dbh.session().flush( [ug] )
            request.session.flash(
                ('success', 'User %s has been added to group %s as %s.' %
                (user_login, group_name, { 'A': 'an admin', 'M': 'a member'}[role]) )
            )


        except exc.IntegrityError:
            request.session.flash(
                ('warning', 'User %s is already in the group %s.' %
                    (user_login, group_name))
            )

        return HTTPFound(
                location = request.referrer or request.route_url('rhombus.group'))

    elif request.POST and method == 'delete':

        user_ids = [ int(x) for x in request.params.getall('user-ids') ]
        group_id = int(request.params.get('group_id'))

        usergroups = dbh.UserGroup.query(dbh.session()).filter(
            dbh.UserGroup.user_id.in_( user_ids), dbh.UserGroup.group_id == group_id)


        if usergroups.count() == 0:
            return Response(modal_error)

        return Response(
            modal_delete(
                title = 'Removing Member(s)',
                content = literal(
                    'You are going to remove the following user(s) from group:'
                    '<ul>' +
                    ''.join( '<li>%s</li>' % ug.user.render() for ug in usergroups ) +
                    '</ul>'
                ),
                request = request
            ),
            request = request
        )

    elif request.POST and method == 'delete/confirm':

        user_ids = [ int(x) for x in request.params.getall('user-ids') ]
        group_id = int(request.params.get('group_id'))

        usergroups = dbh.UserGroup.query(dbh.session()).filter(
            dbh.UserGroup.user_id.in_( user_ids), dbh.UserGroup.group_id == group_id)

        logins = []
        failed_logins = []
        for ug in usergroups:
            if ug.user.primarygroup_id == ug.group_id:
                failed_logins.append(
                    'Warning: cannot remove user %s because group %s is the primary group'
                    % (ug.user.login, ug.group.name))
                continue
            logins.append( ug.user.render() )
            dbh.session().delete( ug )

        dbh.session.flush()
        for failed_login in failed_logins:
            request.session.flash(('danger', failed_login))
        if len(logins) > 0:
            request.session.flash(
                ('success', 'User(s) %s has been removed successfully' % '; '.join( logins )))

        return HTTPFound( location = request.referrer or request.route_url( 'rhombus.group'))

    raise RuntimeError('FATAL - programming ERROR')


@roles(SYSADM, GROUP_CREATE, GROUP_MODIFY, GROUP_DELETE)
def role_action(request):

    method = request.params.get('_method', None)
    dbh = get_dbhandler()

    if request.POST and method == 'add-role':

        roleadd_id = int(request.params.get('roleadd_id'))
        group_id = int(request.params.get('group_id'))

        ek = dbh.EK.get(roleadd_id, dbh.session())
        group = dbh.get_group(group_id)
        ek_key = ek.key
        group_name = group.name

        try:
            group.roles.append( ek )
            dbh.session().flush( [group] )
            request.session.flash(
                ('success', 'Role %s has been added to group %s.' %
                    (ek_key, group_name))
            )


        except exc.IntegrityError:
            request.session.flash(
                ('warning', 'Role %s is already in the group %s.' %
                    (ek_key, group_name))
            )

        return HTTPFound(
                location = request.referrer or request.route_url('rhombus.group'))

    elif request.POST and method == 'delete':

        role_ids = [ int(x) for x in request.params.getall('role-ids') ]
        group_id = int(request.params.get('group_id'))

        eks = [ dbh.EK.get(role_id, dbh.session()) for role_id in role_ids ]


        if len(eks) == 0:
            return Response(modal_error)

        return Response(
            modal_delete(
                title = 'Removing Role(s)',
                content = literal(
                    'You are going to remove the following role(s) from group:'
                    '<ul>' +
                    ''.join( '<li>%s</li>' % ek.key for ek in eks ) +
                    '</ul>'
                ),
                request = request
            ),
            request = request
        )

    elif request.POST and method == 'delete/confirm':

        role_ids = [ int(x) for x in request.params.getall('role-ids') ]
        group_id = int(request.params.get('group_id'))

        eks = [ dbh.EK.get(role_id, dbh.session()) for role_id in role_ids ]
        group = dbh.get_group(group_id)

        removes = []
        for ek in eks:
            group.roles.remove( ek )
            removes.append( ek.key )

        dbh.session.flush([group])
        request.session.flash(
            ('success', 'Role(s) %s has been removed successfully' % '; '.join( removes )))

        return HTTPFound( location = request.referrer or request.route_url( 'rhombus.group'))


    raise RuntimeError('FATAL - programming ERROR')


@roles(PUBLIC)
def lookup(request):
    q = request.params.get('q')

    if not q:
        return error_page(request)

    q = '%' + q.lower() + '%'

    dbh = get_dbhandler()
    groups = dbh.Group.query(dbh.session()).filter(dbh.Group.name.ilike(q))

    # formating for select2 consumption

    result = [
        { 'id': g.id, 'text': g.name}
        for g in groups]

    return result


def edit_form(group, dbh, request, readonly=False):

    if group.check_flags(group.f_composite_group):
        # prepare composite list
        ags = [ag for ag in group.associated_groups if ag.role == 'C']
        composite_ids = [ag.assoc_group_id for ag in ags]
        composite_options = [(ag.associated_group.id, '%s' % ag.associated_group.name)
                             for ag in ags]
    else:
        composite_ids = composite_options = []

    eform = form(name='rhombus/group', method=POST,
                 action=request.route_url('rhombus.group-edit', id=group.id),
                 readonly=readonly)
    eform.add(
        fieldset(
            input_hidden(name='rhombus-group_id', value=group.id),
            input_text('rhombus-group_name', 'Group Name', value=group.name),
            input_text('rhombus-group_desc', 'Description', value=group.desc),
            input_textarea('rhombus-group_scheme', 'Scheme', value=group.scheme),
            input_hidden(name='rhombus-group_options', value=1),
            checkboxes('rhombus-group_options_fields', "Options", [
                       (
                           'rhombus-group_composite', 'Composite',
                           group.check_flags(group.f_composite_group)
                       )]),
            input_select('rhombus-group_composite_ids', 'Composite of', multiple=True,
                         options=composite_options, value=composite_ids),
            submit_bar() if not readonly else a('Edit', class_='btn btn-primary offset-md-3',
                                                href=request.route_url('rhombus.group-edit', id=group.id)),
            name="rhombus-group-fieldset"
        )
    )

    jscode = select2_template(tag="rhombus-group_composite_ids", minlen=3,
                              placeholder="Type a group name",
                              parenttag="rhombus-group-fieldset",
                              url=request.route_url('rhombus.group-lookup')
                              )

    return (eform, jscode)


def parse_form( f ):

    d = dict()
    d['id'] = int(f['rhombus-group_id'])
    d['name'] = f['rhombus-group_name']
    d['desc'] = f['rhombus-group_desc']
    d['scheme'] = f['rhombus-group_scheme']

    if 'rhombus-group_options' in f:
        d['flags-on'] = d['flags-off'] = 0
        if 'rhombus-group_composite' in f:
            d['flags-on'] = d['flags-on'] | Group.f_composite_group
            if 'rhombus-group_composite_ids' in f:
                d['composite_ids'] = [ int(i) for i in f.getall('rhombus-group_composite_ids') ]
            else:
                d['composite_ids'] = []
        else:
            d['flags-off'] = d['flags-off'] | Group.f_composite_group

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


def format_roletable(group, request):

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
    role_bar = selection_bar('role-ids', action=request.route_url('rhombus.group-role_action'),
            others = button(label="Add role",
                        class_="btn btn-sm btn-success", id='group-add-role',
                        name='_method', value='add-role', type='button'),
            hiddens=[('group_id', group.id), ])
    role_table, role_js = role_bar.render(role_table)

    role_content = div(class_='form-group')
    role_content.add(
            div('Role',
                literal('''<select id="roleadd_id" name="roleadd_id" class='form-control' style='width:100%;'></select>'''),
                 class_='col-md-9 col-md-offset-1'),
        )
    submit_button = submit_bar('Add role', 'add-role')

    add_role_form = form( name='add-role-form', method='POST',
                            action=request.route_url('rhombus.group-role_action'),
                        )[  role_content,
                            literal('<input type="hidden" name="group_id" value="%d"/>'
                                % group.id),
                            submit_button ]

    role_table = div(
        div(
            literal( render("rhombus:templates/generics/popup.mako",
            {   'title': 'Add role',
                'content': add_role_form,
                'buttons': '',
            }, request = request )),
            id='add-role-modal', class_='modal fade', tabindex='-1', role='dialog'
        ),
        role_table
    )

    role_js = role_js + '''

$('#group-add-role').click( function(e) {
    $('#add-role-modal').modal('show');
});

''' +  '''
  $('#roleadd_id').select2( {
        minimumInputLength: 3,
        placeholder: 'Type a role here',
        dropdownParent: $("#add-role-modal"),
        ajax: {
            url: "%s",
            dataType: 'json',
            data: function(params) { return { q: params.term, g: "@ROLES" }; },
            processResults: function(data, params) { return { results: data }; }
        },
    });
''' % request.route_url('rhombus.ek-lookup')

    return (role_table, role_js)


def format_usertable(group, request):

    user_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('', style="width: 5px;"), th('Login'), th('Role'), th('Name'), th('Primary group')
        ],
        tbody()[
            tuple([ tr()[
                        td(literal('<input type="checkbox" name="user-ids" value="%d" />' % ug.user_id)),
                        td(a(ug.user.login, href=request.route_url('rhombus.user-view', id=ug.user_id))),
                        td(ug.role),
                        td(ug.user.fullname),
                        td(a(ug.user.primarygroup.name,
                            href=request.route_url('rhombus.group-view', id=ug.user.primarygroup_id))),
                    ] for ug in group.usergroups ])
        ]
    ]
    user_bar = selection_bar('user-ids', action=request.route_url('rhombus.group-user_action'),
            others = button(label="Add member",
                        class_="btn btn-sm btn-success", id='group-add-member',
                        name='_method', value='add-member', type='button'),
            hiddens=[('group_id', group.id), ])
    user_table, user_js = user_bar.render(user_table)

    content = div(class_='form-group form-inline')
    content.add(
            div('Login',
                literal('''<select id="useradd_id" name="useradd_id" class='form-control' style='width:100%;'></select>'''),
                 class_='col-md-7 col-md-offset-1'),
            div('Role',
                literal("<select id='useradd_role' name='useradd_role' class='form-control'>"
                        "<option value='M' default>Member</option>"
                        "<option value='A'>Admin</option>"
                        "</select>"),
                class_='col-md-3')
        )
    submit_button = submit_bar('Add member', 'add-member')

    add_member_form = form( name='add-member-form', method='POST',
                            action=request.route_url('rhombus.group-user_action'),
                        )[  content,
                            literal('<input type="hidden" name="group_id" value="%d"/>'
                                % group.id),
                            submit_button ]

    user_table = div(
        div(
            literal( render("rhombus:templates/generics/popup.mako",
            {   'title': 'Add group member',
                'content': add_member_form,
                'buttons': '',
            }, request = request )),
            id='add-member-modal', class_='modal fade', tabindex='-1', role='dialog'
        ),
        #add_user_html,
        user_table
    )

    user_js = user_js + '''

$('#group-add-member').click( function(e) {
    $('#add-member-modal').modal('show');
});

''' +  '''
  $('#useradd_id').select2( {
        minimumInputLength: 3,
        placeholder: 'Type a name here',
        dropdownParent: $("#add-member-modal"),
        ajax: {
            url: "%s",
            dataType: 'json',
            data: function(params) { return { q: params.term }; },
            processResults: function(data, params) { return { results: data }; }
        },
    });
''' % request.route_url('rhombus.user-lookup')

    return (user_table, user_js)


def select2_template(**keywords):
    return  '''
  $('#%(tag)s').select2( {
        minimumInputLength: %(minlen)d,
        placeholder: '%(placeholder)s',
        dropdownParent: $("#%(parenttag)s"),
        ajax: {
            url: "%(url)s",
            dataType: 'json',
            data: function(params) { return { q: params.term }; },
            processResults: function(data, params) { return { results: data }; }
        },
    });
''' % keywords

