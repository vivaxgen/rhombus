<%inherit file="rhombus:templates/base.mako" />

<h2>${h.link_to('Group', request.route_url('rhombus.group'))}: ${group.name}</h2>

<div class='row'>

<div class='col-md-6'>
<h4>Group Info</h4>
${ form }
</div>

<div class='col-md-6'>
<h4>Roles</h4>
${ role_table }
</div>
</div>

<div class='row'>
<div class='col-md-12'><br /><div class='line-separator'></div></div>
<div class='col-md-8'>
<h4>Members</h4>
${ user_table }
</div>

</div>
##
##
<%def name="jscode()">

${ code | n }

</%def>
##
##
<%def name="stylelinks()">
	<link rel="stylesheet" href="/assets/rb/select2/css/select2.min.css" />
	<link rel="stylesheet" href="/assets/rb/css/select2-bootstrap4.min.css" />
</%def>
##
##
<%def name="jslinks()">
	<script src="/assets/rb/select2/js/select2.min.js"></script>
</%def>
##