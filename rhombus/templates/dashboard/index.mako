<%inherit file="rhombus:templates/base.mako" />

<h1> RHOMBUS DashBoard </h1>

<ul>
<li>User class and user management</li>
<li><a href="${request.route_url('rhombus.group')}">Group management</a></li>
<li><a href="${request.route_url('rhombus.ek')}">Enumerated Key management</a></li>
</ul>
