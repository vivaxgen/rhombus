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
  <!-- rhombus:templates/base.mako -->
  <head>
  <meta charset="utf-8" />
  <title>${request.get_resource('rhombus.title', None) or "Rhombus - utility library for Pyramid web framework"}</title>
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />

  <!-- styles -->
  <link href="/assets/rb/bootstrap/css/bootstrap.min.css" rel="stylesheet" />
  <link href="/assets/rb/fontawesome/css/all.min.css" rel="stylesheet" />
  <link href="/assets/rb/fonts/source-sans-pro.css" rel="stylesheet" />
  <link href="${request.static_url('rhombus:static/css/custom.css')}" rel="stylesheet" />

  ${self.stylelinks()}

  </head>
  <body>

    <!-- Static navbar -->

    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-2">
      <div class="container-fluid">
        <a class="navbar-brand" href="/">${request.get_resource('rhombus.title', None) or "Rhombus - utility library for Pyramid web framework"}</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarSupportedContent">
          <ul class="navbar-nav me-auto">
          </ul>
          <div class="d-flex">
            ${user_menu(request)}
          </div>
        </div>
      </div>
    </nav>

    <div class="container-fluid">

      <div class="row"><div class="col-md-12">
      ${flash_msg()}
      </div></div>

      <div class="row"><div class="col-md-12">
        ${next.body()}
      </div>

    </div>

  ${self.scriptlinks()}

  </body>

</html>
%endif

##
##
<%def name="stylelinks()">
</%def>
##
##
<%def name="scriptlinks()">
    <script src="/assets/rb/js/jquery-3.6.0.min.js"></script>
    <script src="https://unpkg.com/@popperjs/core@2"></script>
    <script src="/assets/rb/bootstrap/js/bootstrap.bundle.min.js"></script>
    <!-- <script src="${request.static_url('rhombus:static/js/jquery.ocupload-min.js')}"></script> -->
    ${self.jslinks()}
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
   <div class="alert alert-${msg_type} alert-dismissible fade show" role="alert">
     ${msg_text}
     <button type="button" class="close" data-dismiss="alert" aria-label="Close">
       <span aria-hidden="true">&times;</span>
     </button>
   </div>
  % endfor

% endif
</%def>

##
<%def name='jscode()'>
</%def>

##
<%def name="jslinks()">
</%def>
