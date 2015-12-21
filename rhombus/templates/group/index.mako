<%inherit file="rhombus:templates/base.mako" />

<h2>Group Listing</h2>

<div class='row'><div class='col-md-12'>

  ${ html }

</div></div>


##
##  START OF METHODS
##
<%def name="stylelink()">
  <link href="${request.static_url('genaf:static/datatables/datatables.min.css')}" rel="stylesheet" />  
</%def>
##
##
<%def name="jslink()">
<script src="${request.static_url('genaf:static/datatables/datatables.min.js')}"></script>
</%def>
##
##
<%def name="jscode()">
  ${code | n}
</%def>
##
##
