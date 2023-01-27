<%inherit file="rhombus:templates/plainbase.mako" />

<h2>ACCESS ERROR</h2>

<p>You are not authenticated in this system! Please login first.</p>

% if text:
  <p>${text}</p>
% endif
