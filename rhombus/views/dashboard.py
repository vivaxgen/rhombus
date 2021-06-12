import logging

log = logging.getLogger(__name__)

from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPForbidden

from rhombus.views import roles
from rhombus.lib.roles import *
from rhombus.lib.tags import *



#@roles( SYSADM, SYSVIEW )
def index(request):

    user = request.user

    if not user:
        import rhombus.views.home
        return rhombus.views.home.login(request)

    if not user.has_roles( SYSADM, SYSVIEW, DATAADM, DATAVIEW,
                    EK_VIEW, USERCLASS_VIEW, USER_VIEW, GROUP_VIEW ):
        raise HTTPForbidden(
            'You are not authorized to access the dashboard. '
            'Please ask site administrator if you believe you need access to system dashboard!')

    ul_list = ul()
    if user.has_roles( SYSADM, SYSVIEW, DATAADM, DATAVIEW, USERCLASS_VIEW ):
        ul_list.add( li(a('User class management',
                            href=request.route_url('rhombus.userclass'))))
    if user.has_roles( SYSADM, SYSVIEW, DATAADM, DATAVIEW, USER_VIEW ):
        ul_list.add( li(a('User management',
                            href=request.route_url('rhombus.user'))))
    if user.has_roles( SYSADM, SYSVIEW, DATAADM, DATAVIEW, GROUP_VIEW ):
        ul_list.add( li(a('Group management',
                            href=request.route_url('rhombus.group'))))
    if user.has_roles( SYSADM, SYSVIEW, DATAADM, DATAVIEW, EK_VIEW ):
        ul_list.add( li(a('Enumerated Key management',
                            href=request.route_url('rhombus.ek')))) 

    html = div()[
        h1('Rhombus Dashboard'),
        ul_list
    ]

    return render_to_response( "rhombus:templates/generics/page.mako",
        {
            'html': html,
        },
        request = request )
