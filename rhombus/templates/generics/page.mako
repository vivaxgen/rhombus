<%inherit file="rhombus:templates/base.mako" />

${ content | n }

##
<%def name="stylelink()">
  <link href="${request.static_url('rhombus:static/rst/rst.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/rst/theme.css')}" rel="stylesheet" />
</%def>
##