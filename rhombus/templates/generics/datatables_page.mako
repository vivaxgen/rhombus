<%inherit file="rhombus:templates/base.mako" />

<h2>${title or ''}</h2>

<div class='row'><div class='col-md-10'>

  ${ html }

</div></div>


##
##  START OF METHODS
##
<%def name="stylelinks()">
  <link href="/assets/rb/datatables/datatables.min.css" rel="stylesheet" />
</%def>
##
##
<%def name="jslinks()">
	<script src="/assets/rb/datatables/datatables.min.js"></script>
</%def>
##
##
<%def name="jscode()">
  ${code | n}
</%def>
##
##
