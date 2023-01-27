

from pyramid.renderers import render_to_response

from rhombus.lib.exceptions import *
from rhombus.lib.utils import get_dbhandler

import transaction
from datetime import datetime


# error view handler

# utilities

def authn_or_authr(request):
    """ return templ (for not authorized or not-authenticated), login and text """
    userinstance = request.identity
    if userinstance:
        templ = 'rhombus:templates/generics/not_authorized.mako'
        login = userinstance.login
        text = f"Your login [{login}] is not authorized to access this resource."
    else:
        templ = 'rhombus:templates/generics/not_authenticated.mako'
        login = ''
        text = "You have not been authenticated in this system."
    return templ, login, text


# pages with exception handlers

def syserror_page(exc, request):
    transaction.abort()
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/syserror_page.mako',
                              {'text': text, 'stamp': str(datetime.now())},
                              request=request)


def usererror_page(exc, request):
    transaction.abort()
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/error_page.mako',
                              {'text': text, 'stamp': str(datetime.now())},
                              request=request)


def dberror_page(exc, request):
    # XXX: clear all cache first, release all db locks (if applicable)
    transaction.abort()
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/error_page.mako',
                              {'text': text, 'stamp': str(datetime.now())},
                              request=request)


def autherror_page(exc, request):
    transaction.abort()
    # check if request has been authenticated
    template, login, text = authn_or_authr(request)
    text = (exc.args[0] if exc.args else str(exc)) or text
    return render_to_response('rhombus:templates/generics/not_authorized.mako',
                              {'text': text, 'stamp': str(datetime.now())},
                              request=request)


# pages with simple text

def error_page(request, text=''):
    transaction.abort()
    return render_to_response('rhombus:templates/generics/error_page.mako',
                              {'text': text, 'stamp': str(datetime.now())},
                              request=request)


def not_authorized(request, text=''):
    transaction.abort()
    templ, login, err_text = authn_or_authr(request)
    text = text or err_text
    return render_to_response(templ,
                              {'text': text, 'login': login},
                              request=request)


# pages with forwarding / refreshing

def forwarding_page(request, text='', url='', delay=5):
    return render_to_response('rhombus:templates/generics/forwarding_page.mako',
                              {'msg': text, 'url': url, 'delay': delay},
                              request=request)


def refreshing_page(request, text='', delay=5):
    return render_to_response('rhombus:templates/generics/refreshing_page.mako',
                              {'text': text, 'delay': delay}, request=request)

# EOF
