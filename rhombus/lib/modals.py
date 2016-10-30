
from rhombus.lib.tags import *

from pyramid.renderers import render


def popup(title, content, footer=None, request=None):

    return literal( render("rhombus:templates/generics/popup.mako",
            {   'title': title,
                'content': content,
                'buttons': footer if footer else '',
            }, request = request ))

def modal_delete(title, content, request):
    return popup(
        title = title,
        content = content,
        footer = literal(
            '<button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button>'
            '<button class="btn btn-danger" type="submit" name="_method" value="delete/confirm">'
            'Confirm Delete</button>'),
        request = request
    )