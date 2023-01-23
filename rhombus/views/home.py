
from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from rhombus.views import roles
from rhombus.lib.roles import SYSADM, SYSVIEW
from rhombus.models.user import UserClass, UserInstance
from rhombus.lib.utils import get_dbhandler, random_string
from rhombus import configkeys as ck

from urllib.parse import urlparse
import time

import logging
log = logging.getLogger(__name__)


def index(request):
    return render_to_response("rhombus:templates/home.mako", {}, request=request)


@roles(SYSADM, SYSVIEW)
def panel(request):
    return render_to_response("rhombus:templates/panel.mako", {}, request=request)


def login(request):
    """ login boilerplate
        fields:
            login
            password
            domain
            came_from
    """

    dbh = get_dbhandler()

    msg = None
    referrer = request.referrer

    # set came_from
    came_from = request.params.get('came_from', referrer) or '/'
    userclass_name = request.params.get('userclass', None)
    if came_from == '/login':
        came_from = '/'

    # override with came_from in session
    came_from_session = request.session.get('came_from', None)
    if came_from_session:
        came_from = came_from_session
    else:
        request.session['came_from'] = came_from

    login = request.params.get('login', '')
    if '/' in login:
        login, userclass_name = login.split('/')
    elif '@' in login:
        # find based on email
        users = dbh.get_user_by_email(login)
        if len(users) > 1:
            # email is used by more than 1 users
            msg = 'Email address is used by multiple users!'
        elif len(users) == 1:
            user = users[0]
            login, userclass_name = user.login, user.userclass.domain
        else:
            msg = 'Email address does not match with any users'
    elif userclass_name is None:
        userclass_name = request.registry.settings.get(ck.rb_default_userclass, '_SYSTEM_')

    if request.POST and msg is None:

        passwd = request.params.get('password', '')
        userclass_id = int(request.params.get('domain', 1))

        userclass = dbh.get_userclass(userclass_name)

        if userclass:

            userinstance = userclass.auth_user(login, passwd)

            if userinstance is not None:
                # headers = set_user_headers(userinstance, request)
                headers = remember(request, userinstance)
                if came_from:
                    o1 = urlparse(came_from)
                    o2 = urlparse(request.host_url)
                    if o1.netloc.lower() == o2.netloc.lower():
                        request.session.flash(
                            ('success', 'Welcome %s!' % userinstance.login)
                        )
                del request.session['came_from']
                return HTTPFound(location=came_from,
                                 headers=headers)

            msg = 'Invalid username or password!'

        else:
            msg = 'Invalid userclass'

    return render_to_response("rhombus:templates/login.mako",
                              {'msg': msg, 'came_from': came_from,
                               'login': '%s' % (login)},
                              request=request)


def logout(request):
    headers = forget(request)
    if request.registry.settings.get(ck.rb_authmode, None) == 'master':
        redirect = request.params.get('redirect', None)
        if not redirect:
            redirect = request.referrer or '/'
        return HTTPFound(location=redirect, headers=headers)
    redirect = request.referrer or '/'
    return HTTPFound(location=redirect,
                     headers=headers)


def confirm(request):
    """ return (status, userinfo) tuple with status as boolen for confirmed (True)
        or unconfirmed (False), and userinfo is a list with the following content:
        [ lastname, firstname, email, institution,
            { group: role, group: role}  # groups where user is member,
            [ group, group, ...]         # groups where user is not member
        ]
    """

    token = request.params.get('principal', '')
    print('confirmation request for:', token)
    userinfo = request.params.get('userinfo', 0)
    if not token:
        return [False, []]

    key = token.encode('ASCII')
    userinstance = request.auth_cache.get(key, None)

    if not userinstance:
        return [False, []]

    if userinfo:
        dbh = get_dbhandler()
        user = dbh.get_user(userinstance.id)
        # prepare for group sync

        usergroups = {}
        for ug in user.usergroups:
            usergroups[ug.group.name] = ug.role
        syncgroups = sorted(
            [grp_name for grp_name in [g.name for g in dbh.get_groups()]
             if grp_name.startswith('sync:')]
        )
        group_ins = {}
        group_out = []
        print(usergroups, syncgroups)
        for sg in syncgroups:
            if sg in usergroups:
                group_ins[sg[5:]] = usergroups[sg]
            else:
                group_out.append(sg[5:])

        userinfo = [user.lastname, user.firstname, user.email, user.institution,
                    group_ins, group_out]
    else:
        userinfo = []

    return [True, userinfo]


def rhombus_css(request):
    """ this will update session, preventing time-out """

    user = request.identity
    if user:
        # unauthenticated_userid == autheticated_userid
        key = request.unauthenticated_userid.decode('ASCII')
        # refresh cache expiration
        request.auth_cache.set(key, user)

    return ""


def rhombus_js(request):

    return rhombus_css(request)


def set_user_headers(userinstance, request):
    """ create token, set user and return http header """

    assert isinstance(userinstance, UserInstance)
    token = '|'.join(
        [userinstance.login, userinstance.domain, str(time.time()), random_string(128)]
    )
    request.set_user(token, userinstance)
    return remember(request, token)
