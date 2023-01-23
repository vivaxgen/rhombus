
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPForbidden

from rhombus.views import roles
from rhombus.lib import roles as r
from rhombus.lib.tags import ul, div, h1, li, a

import logging
log = logging.getLogger(__name__)


# @roles( SYSADM, SYSVIEW )
def index(request):

    user = request.identity

    if not user:
        import rhombus.views.home
        return rhombus.views.home.login(request)

    if not user.has_roles(r.SYSADM, r.SYSVIEW, r.DATAADM, r.DATAVIEW,
                          r.EK_VIEW, r.USERCLASS_VIEW, r.USER_VIEW, r.GROUP_VIEW):
        raise HTTPForbidden(
            'You are not authorized to access the dashboard. '
            'Please ask site administrator if you believe you need access to system dashboard!')

    ul_list = ul()
    if user.has_roles(r.SYSADM, r.SYSVIEW, r.DATAADM, r.DATAVIEW, r.USERCLASS_VIEW):
        ul_list.add(li(a('User class management',
                         href=request.route_url('rhombus.userclass'))))
    if user.has_roles(r.SYSADM, r.SYSVIEW, r.DATAADM, r.DATAVIEW, r.USER_VIEW):
        ul_list.add(li(a('User management',
                         href=request.route_url('rhombus.user'))))
    if user.has_roles(r.SYSADM, r.SYSVIEW, r.DATAADM, r.DATAVIEW, r.GROUP_VIEW):
        ul_list.add(li(a('Group management',
                         href=request.route_url('rhombus.group'))))
    if user.has_roles(r.SYSADM, r.SYSVIEW, r.DATAADM, r.DATAVIEW, r.EK_VIEW):
        ul_list.add(li(a('Enumerated Key management',
                         href=request.route_url('rhombus.ek'))))

    html = div()[
        h1('Rhombus Dashboard'),
        ul_list
    ]

    return render_to_response("rhombus:templates/generics/page.mako",
                              {'html': html, },
                              request=request)

# EOF
