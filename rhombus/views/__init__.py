import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response

from rhombus.lib.roles import *
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.tags import *

        

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



CLASS = 'class_'

def container(*args, **kwargs):
    if CLASS in kwargs:
        class_ = 'container ' + kwargs[CLASS]
        del kwargs[CLASS]
    else:
        class_ = 'container'
    return div(*args, class_=class_, **kwargs)

def row(*args, **kwargs):
    if CLASS in kwargs:
        class_ = 'row ' + kwargs[CLASS]
        del kwargs[CLASS]
    else:
        class_ = 'row'
    return div(*args, class_=class_, **kwargs)

def button(*args, **kwargs):
    if CLASS in kwargs:
        class_ = 'btn btn-info ' + kwargs[CLASS]
        del kwargs[CLASS]
    else:
        class_ = 'btn btn-info'
    return span(*args, class_=class_, **kwargs)

