<%inherit file="rhombus:templates/base.mako" />

<h2>SYSTEM ERROR</h2>

<p>System error has been encountered. Please notify your administrator</p>

% if text:
  <p>Additional notice of the error has been logged as:</p>
  ${text}
% endif
