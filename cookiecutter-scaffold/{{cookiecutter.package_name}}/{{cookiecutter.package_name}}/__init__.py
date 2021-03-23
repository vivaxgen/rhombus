from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from rhombus import init_app
from rhombus.lib.utils import cerr, cout, get_dbhandler
from rhombus.models.core import set_func_userid

# set configuration and dbhandler
from {{cookiecutter.package_name}}.scripts import run

# initialize view
from {{cookiecutter.package_name}}.views import *


def includeme( config ):
    """ this configuration must be included as the last order
    """

    set_func_userid( get_userid_func )

    config.add_static_view('static', 'static', cache_max_age=3600)

    # override assets here
    config.override_asset('rhombus:templates/base.mako', '{{cookiecutter.package_name}}:templates/base.mako')
    config.override_asset('rhombus:templates/plainbase.mako', '{{cookiecutter.package_name}}:templates/plainbase.mako')

    # add route and view for home ('/'), /login and /logout
    config.add_route('home', '/')
    config.add_view('{{cookiecutter.package_name}}.views.home.index', route_name='home')

    config.add_route('login', '/login')
    config.add_view('{{cookiecutter.package_name}}.views.home.login', route_name='login')

    config.add_route('logout', '/logout')
    config.add_view('{{cookiecutter.package_name}}.views.home.logout', route_name='logout')

    # below are example for route for class-based viewer
    # the same thing can be achieved using add_view_route_class()

    config.add_route('post-add', '/add')
    config.add_view('{{cookiecutter.package_name}}.views.post.PostViewer', attr='add', route_name='post-add')

    config.add_route('post-edit', '/posts/{id}@@edit')
    config.add_view('{{cookiecutter.package_name}}.views.post.PostViewer', attr='edit', route_name='post-edit')

    config.add_route('post-view', '/posts/{id}')
    config.add_view('{{cookiecutter.package_name}}.views.post.PostViewer', attr='index', route_name='post-view')


    # add additional routes and views here


def get_userid_func():
    return get_dbhandler().session().user.id


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    cerr('{{cookiecutter.package_name}} main() is running...')

    # attach rhombus to /mgr url, include custom configuration
    config = init_app(global_config, settings, prefix='/mgr'
                    , include = includeme, include_tags = [ '{{cookiecutter.package_name}}.includes' ])

    return config.make_wsgi_app()
