## -*- coding: utf-8 -*-
<!DOCTYPE html>
<html lang="en">
  <head>
  <meta charset="utf-8" />
  <title>${ title or "Rhombus - utility library for Pyramid web framework" }</title>
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />

  <!-- styles -->
  <link href="/assets/rb/bootstrap/css/bootstrap.min.css" rel="stylesheet" />

  <!-- stylelink() -->
  ${self.stylelink()}
  <!-- /stylelink() -->


  </head>
  <body>
    <div class="container-fluid">
    ${next.body()}
    </div>
  </body>
    ${self.scriptlinks()}
</html>

##
##
<%def name="stylelink()">
</%def>
##
##
<%def name="scriptlinks()">
    <script src="/assets/rb/js/jquery-3.6.0.min.js"></script>
    <script src="/assets/rb/js/popper.min.js"></script>
    <script src="/assets/rb/bootstrap/js/bootstrap.bundle.min.js"></script>
    ${self.jslink()}
    <script type="text/javascript">
        //<![CDATA[
        ${self.jscode()}
        //]]>
    </script>
</%def>
##
##
<%def name="jslink()">
</%def>
##
##
<%def name='jscode()'>
</%def>
