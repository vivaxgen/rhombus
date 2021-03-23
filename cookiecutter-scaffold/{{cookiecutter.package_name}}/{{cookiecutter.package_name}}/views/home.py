
from {{cookiecutter.package_name}}.views import *

from rhombus.views.home import login as rb_login, logout as rb_logout

from .post import list_posts

def index(request):

    return render_to_response('{{cookiecutter.package_name}}:templates/generic_page.mako',
                {
                    'html': list_posts(request),
                }, request = request
    )

def login(request):
    return rb_login(request)

def logout(request):
    return rb_logout(request)
