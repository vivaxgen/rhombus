

from pyramid.renderers import render_to_response

from rhombus.lib.exceptions import *
from rhombus.lib.utils import get_dbhandler

import transaction

# error view handler

# pages with exception handlers

def syserror_page(exc, request):
    transaction.abort()
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/syserror_page.mako',
        { 'text': text }, request = request )

def usererror_page(exc, request):
    transaction.abort()
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/error_page.mako',
        { 'text': text }, request = request )

def dberror_page(exc, request):
    # XXX: clear all cache first, release all db locks (if applicable)
    transaction.abort()
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/error_page.mako',
        { 'text': text } )

# pages with simple text

def error_page(request, text=''):
    transaction.abort()
    return render_to_response('rhombus:templates/generics/error_page.mako',
	{ 'text': text }, request = request )

def not_authorized(request, text=''):
    transaction.abort()
    return render_to_response('rhombus:templates/generics/not_authorized.mako',
        { 'text': text }, request = request )


# pages with forwarding / refreshing

def forwarding_page(request, text='', url='', delay=5):
    return render_to_response('rhombus:templates/generics/forwarding_page.mako',
        { 'msg': text, 'url': url, 'delay': delay }, request = request )


def refreshing_page(request, text='', delay=5):
    return render_to_response('rhombus:templates/generics/refreshing_page.mako',
        { 'text': text, 'delay': delay }, request = request )






