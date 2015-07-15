

from pyramid.renderers import render_to_response

from rhombus.lib.exceptions import *

# error view handler

# pages with exception handlers

def syserror_page(exc, request):
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/syserror_page.mako',
        { 'text': text } )

def usererror_page(exc, request):
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/usererror_page.mako',
        { 'text': text } )

def dberror_page(exc, request):
    # XXX: clear all cache first, release all db locks (if applicable)
    text = exc.args[0] if exc.args else ""
    return render_to_response('rhombus:templates/generics/error_page.mako',
        { 'text': text } )

# pages with simple text

def error_page(request, text=''):
    return render_to_response('rhombus:templates/generics/error_page.mako',
	{ 'text': text }, request = request )

def not_authorized(text=''):
    return render_to_response('rhombus:templates/generics/not_authorized.mako',
        { 'text': text } )


# pages with forwarding / refreshing

def forwarding_page(text='', url='', delay=5):
    return render_to_response('rhombus:templates/generics/forwarding_page.mako',
        { 'text': text, 'url': url, 'delay': delay } )


def refreshing_page(text='', delay=5):
    return render_to_response('rhombus:templates/generics/refreshing_page.mako',
        { 'text': text, 'delay': delay } )






