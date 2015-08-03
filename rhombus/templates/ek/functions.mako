<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, checkboxes, submit_bar, input_show, input_textarea, textarea_show, button_edit" />


##
<%def name="list_eks(eks, ek=None)">
<form method='post' action='${request.route_url("rhombus.ek-action")}'>
% if ek:
    ${selection_bar('ek',
        ('Add key', request.route_url("rhombus.ek-edit", id=0, _query = {'member_of_id': ek.id})))}
% else:
    ${selection_bar('ek',
        ('Add key', request.route_url("rhombus.ek-edit", id=0)))}
% endif
<table id="ek-list" class="table table-striped table-condensed">
<thead><tr><th></th><th>Key</th><th>Description</th></tr></thead>
<tbody>
% for k in eks:
    <tr><td><input type="checkbox" name="ek-ids" value='${k.id}' /> </td>
        <td><a href="${request.route_url('rhombus.ek-view', id=k.id)}">${k.key}</a></td>
        <td>${k.desc}</td>
    </tr>
% endfor
</tbody>
</table>
</form>
</%def>


##
<%def name="list_eks_js()">
  ${selection_bar_js('ek', 'ek-ids')}
</%def>


##
<%def name="edit_ek(ek)">
${show_parent(ek)}
<form method='post' class='form-horizontal'
    action='${request.route_url("rhombus.ek-save", id=ek.id)}'>
  <fieldset>
    ${input_hidden('ek.id', value=ek.id)}
    ${input_hidden('ek.member_of_id', value=ek.member_of_id)}
    ${input_text('ek.key', 'Enum Key', value=ek.key)}
    ${input_text('ek.desc', 'Description', value=ek.desc)}
    ${checkboxes('options', '', [ ('ek.syskey', 'System key', ek.syskey ) ])}
    ${input_textarea('ek.data', 'Aux Data', value=ek.data or '')}
    ${submit_bar()}
  </fieldset>
</form>
</%def>


##
<%def name="show_ek(ek)">
${show_parent(ek)}
<form class='form-horizontal'>
  <fieldset>
    ${input_show('Enum Key', ek.key)}
    ${input_show('Description', ek.desc)}
    ${input_show('System key', 'Yes' if ek.syskey else 'No')}
    % if ek.data:
    ${textarea_show('Aux Data', ek.data)}
    % endif
    ${button_edit('Edit', request.route_url('rhombus.ek-edit', id=ek.id))}
  </fieldset>
</form>
</%def>


##
<%def name="show_parent(ek)">
% if ek.member_of_id:
    <p>Member of: <a href="${request.route_url('rhombus.ek-view', id=ek.member_of_id)}">${ek.get(ek.member_of_id).key}</a></p>
% endif
</%def>
