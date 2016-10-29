__copyright__ = '''
__init__.py - Rhombus SQLAlchemy main init module

(c) 2011 - 2015 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''


from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.session import SignedCookieSessionFactory
from pyramid.events import BeforeRender

import dogpile.cache
import dogpile.cache.util

from rhombus.lib.utils import cout, cerr, get_dbhandler
from rhombus.lib import helpers as h


def includeme( config ):

    cerr('rhombus configuration with prefix: %s' % config.route_prefix)

    config.include('pyramid_mako')
    config.add_static_view(name='rhombus_static', path="rhombus:static/")

    session_factory = SignedCookieSessionFactory('Rh0S35s1On')
    config.set_session_factory(session_factory)

    # configure RbRequest

    # configure exception views if debugtoolbar is not enabled
    settings = config.get_settings()
    if 'debugtoolbar.includes' not in settings:
        config.add_view('rhombus.views.generics.usererror_page', context=RuntimeError)

    # configure routes & views

    if config.route_prefix:
        config.add_route('rhombus.dashboard', '/')
        config.add_view('rhombus.views.dashboard.index', route_name = 'rhombus.dashboard')

    add_route_view( config, 'rhombus.views.group', 'rhombus.group',
        '/group',
        '/group/@@action',
        '/group/@@lookup',
        '/group/{id}@@edit',
        '/group/{id}@@save',
        ('/group/{id}', 'view'),
    )

    add_route_view( config, 'rhombus.views.ek', 'rhombus.ek',
        '/ek',
        '/ek/@@action',
        '/ek/@@lookup',
        '/ek/{id}@@edit',
        '/ek/{id}@@save',
        ('/ek/{id}', 'view'),
    )

    add_route_view( config, 'rhombus.views.userclass', 'rhombus.userclass',
        '/userclass',
        '/userclass/@@action',
        '/userclass/{id}@@edit',
        ('/userclass/{id}', 'view'),
    )

    add_route_view( config, 'rhombus.views.user', 'rhombus.user',
        '/user',
        '/user/@@action',
        '/user/@@passwd',
        ('/user/@@lookup', 'lookup', 'json'),
        '/user/{id}@@edit',
        #'/user/{id}@@passwd',
        ('/user/{id}', 'view'),
    )


def add_route_view( config, view_module, prefix_name, *routelist):
    for route_args in routelist:
        renderer = None
        if type(route_args) == str:
            url = route_args
            if '@@' in route_args:
                view_name = route_args.split('@@')[-1]
                route_name = '%s-%s' % (prefix_name, view_name)
            else:
                view_name = 'index'
                route_name = prefix_name
        else:
            url = route_args[0]
            view_name = route_args[1]
            route_name = '%s-%s' % (prefix_name, view_name)
            if len(route_args) > 2:
                renderer = route_args[2]

        config.add_route(route_name, url)
        config.add_view( '%s.%s' % (view_module, view_name),
                route_name = route_name,
                renderer = renderer )



def init_app(global_config, settings, prefix=None, dbhandler_factory = get_dbhandler):
    """ initialize application

        it is encouraged to execute the following method first if it is demeed necessary
        before calling init_app():
            set_initdb_func()

        this function MUST be called AFTER doing multiprocessing forking/init
        and each process needs to call this function independently
    """

    # init dogpile.cache

    authcache = dogpile.cache.make_region(
                key_mangler = dogpile.cache.util.sha1_mangle_key)
    cache = dogpile.cache.make_region(
                key_mangler = dogpile.cache.util.sha1_mangle_key)

    authcache.configure_from_config( settings, 'rhombus.authcache.' )
    cache.configure_from_config( settings, 'dogpile.cache.' )

    # init database
    dbh = dbhandler_factory( settings )

    auth_policy = AuthTktAuthenticationPolicy(
        secret = settings['rhombus.authsecret'],
        callback = lambda req, uid: req.user(),
        hashalg = 'sha512' )

    config = Configurator(settings = settings,
        authentication_policy = auth_policy)

    config.set_request_factory(RhoRequest)
    config.add_request_method(userobj_factory(authcache), 'user', reify=True)
    config.add_request_method(userobj_setter(authcache), 'set_user')
    config.add_request_method(userobj_deleter(authcache), 'del_user')

    config.add_subscriber( add_global, BeforeRender )

    config.include( includeme, prefix )

    return config



def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application, and only run by pserve
    """

    config = init_app(global_config, settings)

    #config = Configurator(settings=settings)
    #config.include( includeme )

    #config.include('pyramid_chameleon')
    #config.add_static_view('static', 'static', cache_max_age=3600)
    #config.add_route('home', '/')
    #config.scan()

    config.add_route('home', '/')
    config.add_view('rhombus.views.home.index', route_name = 'home')

    config.add_route('login', '/login')
    config.add_view('rhombus.views.home.login', route_name = 'login')

    config.add_route('logout', '/logout')
    config.add_view('rhombus.views.home.logout', route_name = 'logout')

    return config.make_wsgi_app()



SESS_TICKET = '_rb_tkt-'

class RhoRequest(Request):


    # override authentication mechanism

    # ticket-based data storage

    def get_sess_ticket(self, ticket=None):
        if ticket == None:
            return SESS_TICKET + random_string(8)
        return SESS_TICKET + ticket

    def get_ticket(self, data):
        while True:
            sess_ticket = self.get_sess_ticket()
            if sess_ticket not in self.session:
                self.session[sess_ticket] = data
                break
        return sess_ticket

    def get_data(self, ticket):
        return self.session.get( self.get_sess_ticket(ticket), None )

    def del_ticket(self, ticket):
        try:
            del self.session[ self.get_sess_ticket(ticket) ]
        except KeyError:
            pass

    def get_resource(self, resource_name, default):
        return self.registry.settings.get(resource_name, default)



def userobj_factory(auth_cache):

    def get_userobj(request):

        user_id = request.unauthenticated_userid
        db_session = get_dbhandler().session()
        if user_id is None:
            db_session.user = None
            return None

        user_id = user_id.encode('ASCII')
        userinstance = auth_cache.get(user_id, None)
        if db_session.user and userinstance and db_session.user.id != userinstance.id:
            cerr('WARNING PROGRAMMING ERROR: reuse of db_session.user -> %d >> %d'
                % (db_session.user.id, userinstance.id))
        db_session.user = userinstance
        return userinstance

    return get_userobj


def userobj_setter(auth_cache):

    def set_userobj(request, user_id, userinstance):

        if request.registry.settings['rhombus.authmode'] != 'master':
            raise RuntimeError( 'ERR: only server with Rhombus authmode as master can set '
                                'user instance!')

        user_id = user_id.encode('ASCII')
        auth_cache.set(user_id, userinstance)

    return set_userobj


def userobj_deleter(auth_cache):

    def del_userobj(request):

        if request.registry.settings['rhombus.authmode'] != 'master':
            raise RuntimeError( 'ERR: only server with Rhombus authmode as master can delete '
                                'user instance!')

        user_id = request.unauthenticated_userid
        if user_id is None:
            return

        user_id = user_id.encode('ASCII')
        auth_cache.delete(user_id)

    return del_userobj


def userobj_checker(auth_cache):

    def hasrole_userobj(request, *roles):

        userinstance = request.user
        if userinstance:
            return userinstance.has_role( *roles )
        return False

    return hasrole_userobj


def override_assets( config, settings, asset_list ):
    """ asset_list: [ (cfg, asset, def_overrider), ...]
                eg. [ ('override.base', 'rhombus:templates/base.mako',
                        'rhombus:templates/my_base.mako') ]
                with override.base as optional tag in config file, so that asset can also
                be override using config file
    """

    for cfg, asset, default_override in asset_list:
        override = settings.get(cfg, default_override)
        print("Overriding asset [%s] with [%s]" % (asset, override))
        config.override_asset(
                to_override = asset,
                override_with = override
        )


def add_global(event):
    event['h'] = h
