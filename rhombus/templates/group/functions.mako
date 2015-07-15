<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit" />

##
##
<%def name="list_groups(groups)" >
<form method='post' action='${request.route_url("rhombus.group-action")}'>
${selection_bar('group', ('Add Group', request.route_url("rhombus.group-edit", id=0)))}

<table id="group-list" class="table table-striped table-condensed">
<thead><tr><th></th><th>Group Name</th><th>Members</th></tr></thead>
<tbody>
% for g in groups:
    <tr><td><input type='checkbox' name='group-ids' value='${g.id}' /></td>
        <td>${h.link_to(g.name, request.route_url('rhombus.group-view', id=g.id))}</td>
        <td>${h.link_to(len(g.users), "")}</td>
    </tr>
% endfor
</tbody>
</table>

</form>
</%def>


##
##
<%def name="list_groups_js()" >
  ${selection_bar_js("group", "group-ids")}
</%def>


##
##
<%def name="show_group(group)" >
  <form class="form-horizontal form-condensed">
    <fieldset>
      ${input_show('Group Name', group.name)}
      ${input_show('Description', group.desc)}
      ${textarea_show('Scheme', group.scheme)}
      ${button_edit('Edit', request.route_url('rhombus.group-edit', id=group.id))}
    </fieldset>
  </form>
</%def>

##
##
<%def name="edit_group(group)" >
<form class="form-horizontal form-condensed" method="post"
        action='${request.route_url("rhombus.group-save", id=group.id)}' >
  <fieldset>
    ${input_hidden('rhombus/group.id', '', value=group.id)}
    ${input_text('rhombus/group.name', 'Group Name', value=group.name)}
    ${input_text('rhombus/group.desc', 'Description', value=group.desc)}
    ${input_textarea('rhombus/group.scheme', 'Scheme', value=group.scheme)}
    ${submit_bar()}
  </fieldset>
</form>
</%def>

##
##
<%def name="edit_group_js()">
</%def>

##
##
<%def name="group_form( grp )" >
  <fieldset>
    ${input_hidden('group.id', '', value = grp.id)}
    ${input_text('group.name', 'Name', value = grp.name or '')}
    ${input_text('group.desc', 'Desc', value = grp.desc or '')}
    ${input_textarea('group.scheme', 'Scheme', value = grp.scheme or '')}
    ${submit_bar()}
  </fieldset>
</%def>

##
##
<%def name="group_users( grp )" >
  <table class="table table-striped table-condensed">
  <thead><tr><th></th><th>User</th><th>Role</th></tr></thead>
  <tbody>
  % for m in grp.usergroups:
      <tr>
      <td><input type="checkbox" name="user.ids" value="${m.user.id}" /></td>
      <td>${m.user.render()}</td>
      <td>${m.role}</td>
      </tr>
  % endfor
  </tbody>
  </table>
</%def>

##
##
<%def name="group_roles( grp )" >
  % for r in grp.roles:
    <div class='row'>
      <div class='span4'>${r}</div>
    </div>
  % endfor
</%def>


##
##
<%def name="adduser_form()">
</%def>

##
##
<%def name="select_group(class_='span3')">
  <input id="select_group_id" name="select_group_id" type="hidden" class="${class_}" />
</%def>

##
##
<%def name="select_group_js(obj_id='#select_group_id')">
  $('${obj_id}').select2( {
        minimumInputLength: 3,
        ajax: {
            url: "${request.route_url('rhombus.group-lookup')}",
            dataType: 'json',
            data: function(term, page) { return { q: term }; },
            results: function(data, page) { return { results: data }; }
        },
    });
</%def>

