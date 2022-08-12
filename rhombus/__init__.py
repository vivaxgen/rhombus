__copyright__ = '''
__init__.py - Rhombus SQLAlchemy main init module

(c) 2011 - 2018 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

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

from rhombus.lib.utils import cout, cerr, get_dbhandler, random_string, dbhandler_userid_func, set_func_userid
from rhombus.lib import helpers as h
from rhombus.lib import exceptions as exc
from rhombus.views import generics

from rhombus.scripts import run

_TITLE_ = ''


def includeme(config):

    cerr('rhombus configuration with prefix: %s' % config.route_prefix)

    # configure exception handler view
    config.add_exception_view(generics.autherror_page, exc.AuthError)

    config.include('pyramid_mako')
    config.add_static_view(name='rhombus_static', path="rhombus:static/")

    session_factory = SignedCookieSessionFactory(random_string(64))
    config.set_session_factory(session_factory)

    # configure RbRequest

    # configure exception views if debugtoolbar is not enabled
    settings = config.get_settings()
    if 'debugtoolbar.includes' not in settings:
        cerr('WARN: setting up in full deployment configuration!')
        config.add_view('rhombus.views.generics.usererror_page', context=RuntimeError)
        config.add_view('rhombus.views.generics.syserror_page', context=Exception)

    # configure routes & views

    if config.route_prefix:
        config.add_route('rhombus.dashboard', '/')
    else:
        config.add_route('rhombus.dashboard', '/dashboard')
    config.add_view('rhombus.views.dashboard.index', route_name='rhombus.dashboard')

    add_route_view(
        config, 'rhombus.views.group', 'rhombus.group',
        '/group',
        '/group/@@action',
        '/group/@@user_action',
        '/group/@@role_action',
        ('/group/@@lookup', 'lookup', 'json'),
        '/group/{id}@@edit',
        '/group/{id}@@save',
        ('/group/{id}', 'view'),
    )

    add_route_view(
        config, 'rhombus.views.ek', 'rhombus.ek',
        '/ek',
        '/ek/@@action',
        ('/ek/@@lookup', 'lookup', 'json'),
        '/ek/{id}@@edit',
        '/ek/{id}@@save',
        ('/ek/{id}', 'view'),
    )

    add_route_view(
        config, 'rhombus.views.userclass', 'rhombus.userclass',
        '/userclass',
        '/userclass/@@action',
        '/userclass/{id}@@edit',
        ('/userclass/{id}', 'view'),
    )

    add_route_view(
        config, 'rhombus.views.user', 'rhombus.user',
        '/user',
        '/user/@@action',
        '/user/@@passwd',
        ('/user/@@lookup', 'lookup', 'json'),
        '/user/{id}@@edit',
        # '/user/{id}@@passwd',
        ('/user/{id}', 'view'),
    )

    add_route_view(
        config, 'rhombus.views.gallery', 'rhombus.gallery',
        '/gallery',
    )

    # for overriding assets
    override_assets(
        config, settings,
        [
            ('override.loginpage', 'rhombus:templates/login.mako'),
        ]
    )

    if 'override.assets' in settings:
        assets = settings['override.assets']
        for asset in assets.split('\n'):
            if not asset:
                continue
            asset_pair = [a.strip() for a in asset.split('>')]
            print('overriding: %s >> %s' % (asset_pair[0], asset_pair[1]))
            config.override_asset(asset_pair[0], asset_pair[1])


def add_route_view(config, view_module, prefix_name, *routelist):
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
        config.add_view(
            '%s.%s' % (view_module, view_name),
            route_name=route_name,
            renderer=renderer
        )


def add_route_view_class(config, view_class, prefix_name, *routelist):
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
        config.add_view(
            view_class,
            attr=view_name,
            route_name=route_name,
            renderer=renderer
        )


def init_app(global_config, settings, prefix=None, dbhandler_factory=get_dbhandler,
             include=None, include_tags=None):
    """ initialize application

        it is encouraged to execute the following method first if it is demeed necessary
        before calling init_app():
            set_initdb_func()

        this function MUST be called AFTER doing multiprocessing forking/init
        and each process needs to call this function independently
    """

    # init dogpile.cache
    global session_expiration_time

    authcache = dogpile.cache.make_region(
        key_mangler=dogpile.cache.util.sha1_mangle_key
    )
    cache = dogpile.cache.make_region(
        key_mangler=dogpile.cache.util.sha1_mangle_key
    )

    authcache.configure_from_config(settings, 'rhombus.authcache.')
    session_expiration_time = int(settings['rhombus.authcache.expiration_time'])
    cache.configure_from_config(settings, 'dogpile.cache.')

    # init database
    dbh = dbhandler_factory(settings)

    parent_domain = True if (settings.get('rhombus.authmode', None) == 'master' or
                    settings.get('rhombus.authhost', None)) else False

    auth_policy = AuthTktAuthenticationPolicy(
        secret=settings['rhombus.authsecret'],
        callback=authenticate_user,
        parent_domain=parent_domain,
        cookie_name=settings.get('rhombus.authcookie', 'rb_auth_tkt'),
        hashalg='sha512'
    )

    config = Configurator(
        settings=settings,
        authentication_policy=auth_policy
    )

    config.set_request_factory(RhoRequest)
    config.add_request_method(auth_cache_factory(authcache), 'auth_cache', reify=True)
    config.add_request_method(auth_cache_factory(cache), 'cache', reify=True)
    config.add_request_method(get_userobj, 'user', reify=True)
    config.add_request_method(set_userobj, 'set_user')
    config.add_request_method(del_userobj, 'del_user')
    config.add_request_method(get_authenticated_userobj, 'get_authenticated_userobj')

    config.add_subscriber(add_global, BeforeRender)

    config.include(includeme, prefix)

    # add static assets directory
    if 'assets.directory' in settings:
        config.add_static_view(name='assets', path=settings['assets.directory'])

    if include:
        config.include(include)

    if include_tags:
        import importlib
        for tag in include_tags:
            if tag not in settings:
                continue
            for include_module in settings[tag].split():
                if not include_module:
                    continue
                print('importing: ', include_module)
                M = importlib.import_module(include_module)
                config.include(getattr(M, 'includeme'))

    if 'rhombus.title' in settings:
        global _TITLE_
        _TITLE_ = settings['rhombus.title']

    return config


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application, and only run by pserve
    """

    cerr('rhombus main() is running...')
    set_func_userid(dbhandler_userid_func)

    config = init_app(global_config, settings)

    # Routes below needs to be replicated by library users as necessary

    config.add_route('home', '/')
    config.add_view('rhombus.views.home.index', route_name='home')

    config.add_route('login', '/login')
    config.add_view('rhombus.views.home.login', route_name='login')

    config.add_route('logout', '/logout')
    config.add_view('rhombus.views.home.logout', route_name='logout')

    config.add_route('g_login', '/g_login')
    config.add_view('rhombus.views.google.g_login', route_name='g_login')

    config.add_route('g_callback', '/g_callback')
    config.add_view('rhombus.views.google.g_callback', route_name='g_callback')

    # check if we are running as master
    if settings.get('rhombus.authmode', None) == 'master':

        # add confirmation url
        config.add_route('confirm', '/confirm')
        config.add_view('rhombus.views.home.confirm', route_name='confirm',
                        renderer='json')

        # for authentication expiration time / stamp purpose
        config.add_route('rhombus_js', '/auth-stamp.js')
        config.add_view('rhombus.views.home.rhombus_js', route_name='rhombus_js',
                        renderer='string')
        config.add_route('rhombus_css', '/auth-stamp.css')
        config.add_view('rhombus.views.home.rhombus_js', route_name='rhombus_css',
                        renderer='string')

    return config.make_wsgi_app()


SESS_TICKET = '_rb_tkt-'
session_expiration_time = None


class RhoRequest(Request):

    # override authentication mechanism

    # ticket-based data storage, using separate dogpile.cache

    def get_sess_ticket(self, ticket=None):
        if ticket is None:
            return SESS_TICKET + random_string(8)
        return SESS_TICKET + ticket

    def get_ticket(self, data, ticket=None):
        while True:
            sess_ticket = self.get_sess_ticket(ticket)
            if self.cache.get(sess_ticket) == dogpile.cache.api.NO_VALUE:
                self.cache.set(sess_ticket, data)
                break
        return sess_ticket

    def get_data(self, ticket, expiration_time=None):
        data = self.cache.get(
            self.get_sess_ticket(ticket),
            expiration_time or session_expiration_time
        )
        if data == dogpile.cache.api.NO_VALUE:
            raise KeyError(f"ticket {ticket} is not associated with any data.")
        return data

    def del_ticket(self, ticket):
        try:
            del self.session[self.get_sess_ticket(ticket)]
        except KeyError:
            pass

    def get_resource(self, resource_name, default):
        return self.registry.settings.get(resource_name, default)


def authenticate_user(user_id, request):
    """ this will only be called during request.authenticated_userid """

    return request.get_authenticated_userobj(user_id)


def auth_cache_factory(auth_cache):

    def get_auth_cache(request):

        return auth_cache

    return get_auth_cache


def get_authenticated_userobj(request, token):

    dbh = get_dbhandler()
    db_session = dbh.session()
    if token is None:
        db_session.user = None
        return None

    # get userinstance from current dogpile.cache
    auth_cache = request.auth_cache
    key = token.encode('ASCII')
    userinstance = auth_cache.get(key, session_expiration_time)
    if not userinstance and 'rhombus.authhost' in request.registry.settings:
        # in client mode

        # verify to authentication host
        confirmation = confirm_token(request.registry.settings['rhombus.authhost'], token)
        if confirmation[0]:

            # check the existence of the user
            login, userclass, stamp, randstr = token.split('|')
            user = dbh.get_user('%s/%s' % (login, userclass))
            if user is None:
                # check is userclass is exists, then add the user automatically to user class

                uc = dbh.get_userclass(userclass)
                if uc is None:
                    request.session.flash(
                        (
                            'danger',
                            f'Warning: your current login [{login}] is not registered in this system!'
                        )
                    )
                    return None

                lastname, firstname, email = confirmation[1][:3]
                user = uc.add_user(login, lastname, firstname, email, uc.credscheme['primary_group'])
                request.session.flash(
                    (
                        'success',
                        f'You have been registered to the system under userclass: {uc.domain}'
                    )
                )

            # sync groups for this user if necessary
            added, modified, removed = user.sync_groups(confirmation[1][4], confirmation[1][5])

            # set user
            userinstance = user.user_instance()
            auth_cache.set(key, userinstance)
            request.session.flash(
                (
                    'success',
                    f'You have been authenticated remotely as {userinstance.login}!'
                )
            )
            if added:
                request.session.flash(
                    (
                        'success',
                        'You have been added to group(s): %s.' % ' '.join(added)
                    )
                )
            if modified:
                request.session.flash(
                    (
                        'success',
                        'Your role has been modified in group(s): %s.' % ' '.join(modified)
                    )
                )
            if removed:
                request.session.flash(
                    (
                        'success',
                        'You have been removed from group(s): %s' % ' '.join(removed)
                    )
                )

    db_session.user = userinstance or None

    return userinstance


def get_userobj(request):

    user_id = request.authenticated_userid
    if user_id:
        ui = get_dbhandler().session().user
        return ui

    return None


def set_userobj(request, user_id, userinstance):

    if request.registry.settings.get('rhombus.authhost', None) is not None:
        raise RuntimeError('ERR: only server without Rhombus rhombus.authhost can set '
                           'user instance! Otherwise, please add rhombus.authmode = master '
                           'and remove rhombus.authhost setting.')

    user_id = user_id.encode('ASCII')
    request.auth_cache.set(user_id, userinstance)


def del_userobj(request):

    if request.registry.settings.get('rhombus.authhost', None) is not None:
        raise RuntimeError('ERR: only server without Rhombus rhombus.authhost can delete '
                           'user instance!')

    user_id = request.unauthenticated_userid
    if user_id is None:
        return

    user_id = user_id.encode('ASCII')
    request.auth_cache.delete(user_id)


def hasrole_userobj(request, *roles):

    userinstance = request.user
    if userinstance:
        return userinstance.has_role(*roles)
    return False


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

        if request.registry.settings.get('rhombus.authmode', None) != 'master':
            raise RuntimeError('ERR: only server with Rhombus authmode as master can set '
                               'user instance!')

        user_id = user_id.encode('ASCII')
        auth_cache.set(user_id, userinstance)

    return set_userobj


def userobj_deleter(auth_cache):

    def del_userobj(request):

        if request.registry.settings['rhombus.authmode'] != 'master':
            raise RuntimeError('ERR: only server with Rhombus authmode as master can delete '
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
            return userinstance.has_role(*roles)
        return False

    return hasrole_userobj


def confirm_token(url, token):
    import requests
    r = requests.get(url + '/confirm', params={'principal': token, 'userinfo': 1})
    if not r.ok:
        raise RuntimeError("ERROR: principal authenticator failed to respond properly!")
    return r.json()


def override_assets(config, settings, asset_list):
    """ asset_list: [ (cfg, asset, def_overrider), ...]
                eg. [ ('override.base', 'rhombus:templates/base.mako',
                        'rhombus:templates/my_base.mako') ]
                with override.base as optional tag in config file, so that asset can also
                be override using config file
    """

    for cfg, asset in asset_list:
        override = settings.get(cfg, asset)
        if override == asset:
            continue
        print("Overriding asset [%s] with [%s]" % (asset, override))
        config.override_asset(
            to_override=asset,
            override_with=override
        )


def add_global(event):
    from rhombus.views.user import user_menu
    event['h'] = h
    event['title'] = _TITLE_ or 'Rhombus'
    event['user_menu'] = user_menu

# EOF
