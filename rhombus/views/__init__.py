
import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.lib.roles import *
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.tags import *
from rhombus.views.generics import not_authorized


class not_roles(object):

    def __init__(self, *role_list):
        self.not_roles = role_list

msg_0 = 'Please log in first.'

msg_1 = 'Please notify the administrator if you believe that '\
        'you should be able to access this resource.'


class roles(object):

    def __init__(self, *role_list):
        self.allowed = []
        self.disallowed = []
        for role in role_list:
            if isinstance(role, not_roles):
                self.disallowed.extend(role.not_roles)
            else:
                self.allowed.append(role)

    def __call__(self, wrapped):
        if self.allowed or self.disallowed:
            # need to check the roles
            def _view_with_roles(request, **kw):
                if request.user and request.user.has_roles(*self.disallowed):
                    return not_authorized(request, msg_1)
                if PUBLIC in self.allowed and request.user:
                    return wrapped(request, **kw)
                if not request.user:
                    return not_authorized(request, msg_0)
                if not request.user.has_roles(*self.allowed):
                    return not_authorized(request, msg_1)
                return wrapped(request, **kw)
            return _view_with_roles

        else:
            # no roles, just return the function
            return wrapped


class m_roles(roles):

    def __call__(self, wrapped):
        if self.allowed or self.disallowed:
            # need to check the roles
            def _view_with_roles(inst, **kw):
                request = inst.request
                if request.user and request.user.has_roles(*self.disallowed):
                    return not_authorized(request, msg_1)
                if PUBLIC in self.allowed and request.user:
                    return wrapped(inst, **kw)
                if not request.user:
                    return not_authorized(request, msg_0)
                if not request.user.has_roles(*self.allowed):
                    return not_authorized(request, msg_1)
                return wrapped(inst, **kw)
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

