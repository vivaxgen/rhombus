## -*- coding: utf-8 -*-
% if request and request.is_xhr:
  ${next.body()}

  <script type="text/javascript">
    //<![CDATA[
    ${self.jscode()}
    //]]>
  </script>

% else:
<!DOCTYPE html>
<html lang="en">
  <head>
  <meta charset="utf-8" />
  <title>${ title or "Rhombus - utility library for Pyramid web framework" }</title>
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />

  <!-- styles -->
  <link href="${request.static_url('rhombus:static/bootstrap/css/bootstrap.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/bootstrap/css/bootstrap-theme.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/fonts/source-sans-pro.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/font-awesome-4.5.0/css/font-awesome.min.css')}" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/select2/css/select2.min.css')}" rel="stylesheet" />
  ${self.stylelink()}

  </head>
  <body>
    <div class="container-fluid">
    ${next.body()}
    </div>

  ${self.scriptlinks()}

  </body>

</html>
%endif

##
##
<%def name="stylelink()">
</%def>
##
##
<%def name="scriptlinks()">
    <script src="${request.static_url('rhombus:static/js/jquery.js')}"></script>
    <script src="${request.static_url('rhombus:static/bootstrap/js/bootstrap.min.js')}"></script>
    <script src="${request.static_url('rhombus:static/select2/js/select2.min.js')}"></script>
    <script src="${request.static_url('rhombus:static/js/jquery.ocupload-min.js')}"></script>
    ${self.jslink()}
    <script type="text/javascript">
        //<![CDATA[
        ${self.jscode()}
        //]]>
    </script>
</%def>
##
##
<%def name='flash_msg()'>
% if request.session.peek_flash():

  % for msg_type, msg_text in request.session.pop_flash():
   <div class="alert alert-${msg_type}">
     <a class="close" data-dismiss="alert">×</a>
     ${msg_text}
   </div>
  % endfor

% endif
</%def>

##
<%def name='jscode()'>
</%def>

##
<%def name="jslink()">
</%def>


