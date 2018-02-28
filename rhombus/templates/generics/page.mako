<%inherit file="rhombus:templates/base.mako" />

% if html:
${ html }
% else:
${ content | n }
% endif

##
<%def name="stylelink()">
  <link href="${request.static_url('rhombus:static/rst/rst.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/rst/theme.css')}" rel="stylesheet" />
</%def>
##
##
<%def name="jscode()">
  ${code or '' | n}
</%def>
##
##
