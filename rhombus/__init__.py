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

from pyramid.events import BeforeRender

import dogpile.cache
import dogpile.cache.util

from rhombus import configkeys as ck
from rhombus.lib.utils import cout, cerr, get_dbhandler, random_string, dbhandler_userid_func, set_func_userid
from rhombus.lib import helpers as h
from rhombus.routes import includeme
from rhombus.scripts import run

import time

import logging
logger = logging.getLogger(__name__)

_TITLE_ = ''


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

    authcache.configure_from_config(settings, ck.rb_authcache_)
    session_expiration_time = int(settings[ck.rb_authcache_expiration_time])
    cache.configure_from_config(settings, 'dogpile.cache.')

    # init database
    dbh = dbhandler_factory(settings)

    parent_domain = True if (settings.get(ck.rb_authmode, None) == 'master' or
                             settings.get(ck.rb_authhost, None)) else False

    auth_policy = AuthTktAuthenticationPolicy(
        secret=settings[ck.rb_authsecret],
        callback=authenticate_user,
        parent_domain=parent_domain,
        cookie_name=settings.get(ck.rb_authcookie, 'rb_auth_tkt'),
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
    if ck.assets_directory in settings:
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

    if ck.rb_title in settings:
        global _TITLE_
        _TITLE_ = settings[ck.rb_title]

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
    if settings.get(ck.rb_authmode, None) == 'master':

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
        self.cache.delete(self.get_sess_ticket(ticket))

    def get_resource(self, resource_name, default):
        return self.registry.settings.get(resource_name, default)


class RhoSecurityPolicy(object):
    """ Rhombus Security Policy, which combine auth ticket cookie to obtain local cache,
        compatible for pyramid >= 2.0. This class uses a token to load the actual userinstance
        from local auth cache. The token is composed of "login|domain|login_time|random_string"
    """

    def __init__(self, helper, auth_cache):
        self.helper = helper
        self.auth_cache = auth_cache

    def identity(self, request):
        authtoken = self.helper.authenticated_userid(request)
        if authtoken is None:
            return None
        # TODO: check token for hard expire time here

        userinstance = self.auth_cache.get(authtoken)

        if not userinstance and ck.rb_authhost in request.registry.settings:
            # TODO: in client mode, if userinstance is not yet existed, check to the remote/host
            # autheticator
            raise NotImplementedError()

        return userinstance
        # TODO: check userinstance last stamp

    def authenticated_userid(self, request):
        userinstance = self.identity(request)
        if userinstance is None:
            return None
        return userinstance

    def permits(self, request, context, permission):
        pass

    def remember(self, request, userinstance, **kw):
        authtoken = self._generate_authtoken(userinstance)
        self.auth_cache.set(authtoken, userinstance)
        return self.helper.remember(request, authtoken, **kw)

    def forget(self, request, **kw):
        authtoken = self.helper.authenticated_userid(request)
        if authtoken:
            self.auth_cache.delete(authtoken)
        return self.helper.forget(request, **kw)

    def _generate_authtoken(self, userinstance):
        return f'{userinstance.login}|{userinstance.domain}|{int(time.time())}|{random_string(128)}'

    def _split_authtoken(self, authtoken):
        el = authtoken.split('|')
        return el[0], el[1], int(el[2]), el[3]


def authenticate_user(user_id, request):
    """ this will only be called during request.authenticated_userid """

    return request.get_authenticated_userobj(user_id)


def auth_cache_factory(auth_cache):

    def get_auth_cache(request):

        return auth_cache

    return get_auth_cache


def get_authenticated_userobj(request, token):
    global session_expiration_time

    dbh = get_dbhandler()
    db_session = dbh.session()
    if token is None:
        db_session.user = None
        return None

    # get userinstance from current dogpile.cache
    auth_cache = request.auth_cache
    key = token.encode('ASCII')
    userinstance = auth_cache.get(key, session_expiration_time)
    # if there is no current user, userinstance will be NO_VALUE, which has value of False
    if not userinstance and ck.rb_authhost in request.registry.settings:
        # in client mode

        # verify to authentication host
        confirmation = confirm_token(request.registry.settings[ck.rb_authhost], token)
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
                if type(uc.credscheme) is not dict or 'primary_group' not in uc.credscheme:
                    request.session.flash(
                        (
                            'danger',
                            f'Warning: your current login [{login}] is not registered in this system '
                            f'and automatic remote user registration is disabled. Please contact '
                            f'the system administrator of this system.'
                        )
                    )
                    return None

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

    if userinstance:
        # check if we need to update laststamp
        now = int(time.time())
        logger.info(f'session stamp: {now} - {userinstance.laststamp} = {now - userinstance.laststamp}')
        if (now - userinstance.laststamp) > session_expiration_time * 0.75:
            logger.info(f'> {session_expiration_time * 0.75}')
            # set new timestamp
            userinstance.laststamp = now
            auth_cache.set(key, userinstance)

    db_session.user = userinstance or None

    return userinstance


def get_userobj(request):

    user_id = request.authenticated_userid
    if user_id:
        ui = get_dbhandler().session().user
        return ui

    return None


def set_userobj(request, user_id, userinstance):

    if request.registry.settings.get(ck.rb_authhost, None) is not None:
        raise RuntimeError('ERR: only server without Rhombus rhombus.authhost can set '
                           'user instance! Otherwise, please add rhombus.authmode = master '
                           'and remove rhombus.authhost setting.')

    user_id = user_id.encode('ASCII')
    request.auth_cache.set(user_id, userinstance)


def del_userobj(request):

    if request.registry.settings.get(ck.rb_authhost, None) is not None:
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

        if request.registry.settings.get(ck.rb_authmode, None) != 'master':
            raise RuntimeError('ERR: only server with Rhombus authmode as master can set '
                               'user instance!')

        user_id = user_id.encode('ASCII')
        userinstance.laststamp = int(time.time())
        auth_cache.set(user_id, userinstance)

    return set_userobj


def userobj_deleter(auth_cache):

    def del_userobj(request):

        if request.registry.settings[ck.rb_authmode] != 'master':
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


def add_global(event):
    from rhombus.views.user import user_menu
    event['h'] = h
    event['title'] = _TITLE_ or 'Rhombus'
    event['user_menu'] = user_menu

# EOF
