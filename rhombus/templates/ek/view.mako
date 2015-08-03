<%inherit file="rhombus:templates/base.mako" />
<%namespace file="rhombus:templates/ek/functions.mako" import="show_ek, list_eks, list_eks_js" />

<h2>${h.link_to('Enumerated Key', request.route_url('rhombus.ek'))}</h2>

<div class='row'><div class='span6'>
  ${show_ek(ek)}
</div></div>

<h4>Members</h4>
<div class='row'><div class='span6'>
  ${list_eks(ek.members, ek)}
</div></div>
##
##
<%def name="jscode()">
  ${list_eks_js()}
</%def>
