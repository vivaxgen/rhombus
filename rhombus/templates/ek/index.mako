<%inherit file="rhombus:templates/base.mako" />
<%namespace file="rhombus:templates/ek/functions.mako" import="list_eks, list_eks_js" />

<h2>Enumerated Key</h2>

<div class='row'><div class='span6'>
  ${list_eks(eks)}
</div></div>

##
<%def name="jscode()">
  ${list_eks_js()}
</%def>


