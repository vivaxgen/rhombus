
from rhombus.lib.utils import cout, cerr

# LDAP data:
# { 'sys': 'LDAP', 'host': ..., 'DN': ... }

def validate_by_LDAP(username, passwd, scheme):
    import ldap3
    s = ldap3.Server(host = scheme['host'], get_info=ldap3.ALL)
    c = ldap3.Connection(s, user=scheme['DN'] % username, password = passwd)
    if not c.bind():
        cerr('Failed LDAP authentication for user: %s' % username)
        return False
    return True


# BasicHTTP:
# { 'sys': 'BasicHTTP', 'host': ..., 'realm': ..., 'referrer': ..., 'theme': ... }

def validate_by_basichttp(username, passwd, scheme):
    realm = scheme['realm']    # eg. sp.seaclinicalresearch.org
    url = scheme['host'] # eg. https://sp.seaclinicalresearch.org/default.aspx

    # Create an OpenerDirector with support for Basic HTTP Authentication...
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm=realm,
                          uri=url,
                          user=username,
                          passwd=passwd)
    opener = urllib2.build_opener(auth_handler)
    try:
        opener.open(url)
        return True
    except urllib2.HTTPError:
        return False


# util for adding user automatically
# should return ('lastname', 'firstname', 'email')

def inquire_by_LDAP( username, scheme ):
    import ldap3
    s = ldap3.Server(host = scheme['host'], get_info=ldap3.ALL)
    c = ldap3.Connection(s, auto_bind=True)
    c.search(scheme['DN'] % username, '(objectClass=*)', attributes=['sn', 'givenName', 'mail'])
    if len(c.response) > 0:
        attributes = c.response[0]['attributes']
        return (attributes['sn'][0], attributes['givenName'][0], attributes['mail'][0])
    else:
        return ('', '', '')


def inquire_dummy( username, scheme ):
    return ('', '', '')


authfunc = {
    'LDAP': (validate_by_LDAP, inquire_by_LDAP),
    'BasicHTTP': (validate_by_basichttp, inquire_dummy)
}

