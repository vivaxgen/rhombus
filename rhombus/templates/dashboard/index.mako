<%inherit file="rhombus:templates/base.mako" />

<h1> RHOMBUS DashBoard </h1>

<ul>
<li><a href="${request.route_url('rhombus.userclass')}">User class management</a></li>
<li><a href="${request.route_url('rhombus.user')}">User management</a></li>
<li><a href="${request.route_url('rhombus.group')}">Group management</a></li>
<li><a href="${request.route_url('rhombus.ek')}">Enumerated Key management</a></li>
</ul>
