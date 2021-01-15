<%inherit file="rhombus:templates/base.mako" />

<h2>ACCESS ERROR</h2>

<p>You are not authorized to access this resource!</p>

% if text:
  <p>${text}</p>
% endif
