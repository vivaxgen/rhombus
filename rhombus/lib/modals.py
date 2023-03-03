
from rhombus.lib.tags import literal

from pyramid.renderers import render


def popup(title, content, footer=None, request=None):
    return literal(render("rhombus:templates/generics/popup.mako", {
        'title': title,
        'content': content,
        'buttons': footer if footer else '',
    }, request=request))


def modal_delete(title, content, request, value='delete/confirm'):
    return popup(
        title=title,
        content=content,
        footer=literal(
            '<button class="btn" data-bs-dismiss="modal" type="button" aria-hidden="true">Cancel</button>'
            '<button class="btn btn-danger" type="submit" name="_method" value="%s">'
            'Confirm Delete</button>' % value),
        request=request
    )


def modal_error(title='Error', content='', request=None):
    return popup(
        title=title,
        content=content,
        request=request
    )

# EOF
