import logging

log = logging.getLogger(__name__)

from pyramid.renderers import render_to_response

from rhombus.views import roles
from rhombus.lib.roles import SYSADM, SYSVIEW

@roles( SYSADM, SYSVIEW )
def index(request):

    return render_to_response( "rhombus:templates/dashboard/index.mako",
        {},
        request = request )
