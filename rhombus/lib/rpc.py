
from rhombus.lib.utils import random_string, get_dbhandler
from rhombus import configkeys as ck

import time


# User token management
#
# how to test token via curl
# curl -X POST -H 'Content-Type: application/json' \
# -d '{"jsonrpc":"2.0","id":234,"method":"check_auth","params":["utkn:YPGIt0lFw4HiN7vLaStOdWQXBGCiph_n"]}' \
# http://localhost:6543/rpc | python3 -m json.tool


def generate_user_token(request, user=None):

    user = request.user if user is None else user

    token = 'utkn:' + random_string(32)
    payload = {'create_time': time.time(), 'userinstance': user}
    request.get_ticket(payload, token)
    return token


def revoke_user_token(request, token):
    payload = request.del_ticket(token)


# public function v1

def generate_token(request, login, passwd):

    # check login and passwd
    dbh = get_dbhandler()
    user = dbh.auth_user(login, passwd, request.registry.settings.get(ck.rb_default_userclass, '_SYSTEM_'))
    if user:
        return generate_user_token(request, user)


def check_auth(request, token):
    pass


def revoke_token(request, token):
    return revoke_user_token(request, token)

# EOF
