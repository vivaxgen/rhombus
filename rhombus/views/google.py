import logging

log = logging.getLogger( __name__ )

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from rhombus.models.user import UserClass
from rhombus.views.home import set_user_headers
from rhombus.lib.utils import get_dbhandler
from rhombus.lib.tags import *

from authlib.integrations.requests_client import OAuth2Session


import json, time
from urllib.parse import urlparse

g_authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
g_token_url = "https://www.googleapis.com/oauth2/v4/token"
g_userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
g_scope = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]


def g_login(request):
    """ this is for Google OAuth 2 using requests-oauthlib
    """

    client_id = request.registry.settings.get('rhombus.oauth2.google.client_id', None)
    redirect_uri = request.registry.settings.get('rhombus.oauth2.google.redirect_uri', None)
    if client_id is None or redirect_uri is None:
        return HTTPFound( location='/')

    referrer = request.referrer

    # set came_from
    came_from = request.params.get('came_from', referrer) or '/'
    if came_from == '/g_login':
        came_from = '/'

    # override with came_from in session
    came_from_session = request.session.get('came_from', None)
    if came_from_session:
        came_from = came_from_session
    request.session['came_from'] = came_from

    google = OAuth2Session(client_id, scope=g_scope, redirect_uri=redirect_uri)

    authorization_url, state = google.create_authorization_url(g_authorization_base_url,
        # offline for refresh token
        # force to always make user click authorize
        access_type="offline", prompt="select_account")
    request.session['oauth2_state'] = state

    print('google oauth2:', authorization_url)
    return HTTPFound( location=authorization_url )

def g_callback(request):
    """ this is the redirect URL after google authentication
    """

    client_id = request.registry.settings.get('rhombus.oauth2.google.client_id', None)
    client_secret = request.registry.settings.get('rhombus.oauth2.google.client_secret', None)
    redirect_uri = request.registry.settings.get('rhombus.oauth2.google.redirect_uri', None)

    authresp = request.params.get('authresp', request.url)
    print("google authresp:", authresp)
    print(request.session['oauth2_state'])

    google = OAuth2Session(client_id, scope=g_scope, redirect_uri=redirect_uri,
            state = request.session['oauth2_state'])
    token = google.fetch_token(g_token_url, client_secret = client_secret,
            authorization_response = authresp)

    # we use the token to get the profile first
    r = google.get(g_userinfo_url)
    userinfo = json.loads(r.content)

    # userinfo should has itemss:
    # id, email, verified_email, name, given_name, family_name, picture, locale
    email = userinfo['email']

    dbh = get_dbhandler()
    users = dbh.get_user_by_email(email)
    if len(users) > 1:
        # email is used by more than 1 users
        # we will not allow for now
        raise RuntimeError('There are more than one user with email: %s' % email)
    elif len(users) == 0:
        raise RuntimeError('No user with email: %s' % email)

    userinstance = users[0].user_instance()
    headers = set_user_headers(userinstance, request)
    came_from = request.params.get('came_from', '/')
    if came_from:
        o1 = urlparse(came_from)
        o2 = urlparse(request.host_url)
        if o1.netloc.lower() == o2.netloc.lower():
            request.session.flash(
                ('success', 'Welcome %s!' % userinstance.login)
            )
    del request.session['came_from']
    return HTTPFound( location = came_from,
                    headers = headers )


def g_selectuser(request):
	""" this method is necessary when the gmail address is used by more than
		single user account
	"""

	# part of url is stored in session
	request.session['g_uri']