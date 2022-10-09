<%inherit file="rhombus:templates/plainbase.mako" />

<h2>ACCESS ERROR</h2>

<p>You are not authorized to either access nor process this resource!</p>

% if text:
  <p>${text}</p>
% endif
