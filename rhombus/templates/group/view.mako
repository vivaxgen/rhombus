<%inherit file="rhombus:templates/base.mako" />

<h2>${h.link_to('Group', request.route_url('rhombus.group'))}: ${group.name}</h2>

<div class='row'>

<div class='col-md-6'>
<p>Group Info</p>
${ form }
</div>

<div class='col-md-6'>
<h4>Roles</h4>
<p>List of roles</p>
</div>

<div class='col-md-6'>
<h4>Members</h4>
</div>

</div>
##
##
<%def name="jscode()">

</%def>
