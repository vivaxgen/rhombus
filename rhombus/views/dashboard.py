import logging

log = logging.getLogger(__name__)

from pyramid.renderers import render_to_response

from rhombus.views import roles
from rhombus.lib.roles import SYSADM, SYSVIEW


#@roles( SYSADM, SYSVIEW )
def index(request):

    if not request.user:
        import rhombus.views.home
        return rhombus.views.home.login(request)

    if not request.user.has_roles( SYSADM, SYSVIEW ):
        return error_page(request, 'You are not authorized to access this page!')

    return render_to_response( "rhombus:templates/dashboard/index.mako",
        {},
        request = request )
