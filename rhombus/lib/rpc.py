
from pyramid_rpc.jsonrpc import JsonRpcError

from rhombus.lib.utils import random_string, get_dbhandler
from rhombus import configkeys as ck

import time


# User token management
#
# how to test token via curl
# curl -X POST -H 'Content-Type: application/json' \
# -d '{"jsonrpc":"2.0","id":234,"method":"check_auth","params":["utkn:YPGIt0lFw4HiN7vLaStOdWQXBGCiph_n"]}' \
# http://localhost:6543/rpc | python3 -m json.tool


def get_userinstance_by_token(request, token):
    """ return user, errmsg """

    try:
        payload = request.get_data(token, 12 * 3600)
    except KeyError:
        return None, "token does not exist or is already expired"
    if (time.time() - payload['create_time']) / 3600 > 12:
        return None, "token is expired"
    return payload['userinstance'], ''


def generate_user_token(request, user=None):

    user = request.user if user is None else user

    token = 'utkn:' + random_string(32)
    payload = {'create_time': time.time(), 'userinstance': user}
    request.get_ticket(payload, token)
    return token


def revoke_user_token(request, token):
    request.del_ticket(token)


# public function v1

def generate_token(request, login, passwd):
    """ generate_token can only be used when the system is set as master authenticator,
        otherwise need to use the web interface to get the authentication token """

    # check authentication settings
    if request.registry.settings.get(ck.rb_authmode, '') == 'slave':
        raise JsonRpcError(code=-31001, message='Please use web interface to generate token.')

    # check login and passwd
    dbh = get_dbhandler()
    user = dbh.auth_user(login, passwd, request.registry.settings.get(ck.rb_default_userclass, '_SYSTEM_'))
    if user is None:
        raise JsonRpcError(code=-31002, message='Invalid login/password combination.')

    return generate_user_token(request, user)


def check_token(request, token):
    userinstance, errmsg = get_userinstance_by_token(request, token)
    if userinstance is None:
        return {'auth': False, 'user': None, 'errmsg': errmsg}
    return {'auth': True, 'user': userinstance.login, 'errmsg': None}


def revoke_token(request, token):
    revoke_user_token(request, token)

# EOF
