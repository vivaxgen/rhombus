<%inherit file="rhombus:templates/base.mako" />

<h1>RHOMBUS - addon framework on top of pyramid</h1>


% if request.identity:
  <p>You are authenticated as: ${request.identity.login}</p>
% else:
  <p>You are not authenticated.</p>
% endif
