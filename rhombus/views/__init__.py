import logging
from pyramid.response import Response
from pyramid.renderers import render_to_response

from rhombus.lib.roles import *
from rhombus.lib.utils import get_dbhandler

log = logging.getLogger(__name__)
        

class roles(object):

    def __init__(self, *role_list):
        if role_list:
            self.roles = role_list
        else:
            self.roles = ()

    def __call__(self, wrapped):
        if self.roles:
            # need to check the roles
            def _view_with_roles(request, **kw):
                if PUBLIC in self.roles and request.user:
                    return wrapped(request, **kw)
                if not (request.user and request.user.has_roles(*self.roles)):
                    return Response('Forbidden')
                return wrapped(request, **kw)
            return _view_with_roles

        else:
            # no roles, just return the function
            return wrapped

