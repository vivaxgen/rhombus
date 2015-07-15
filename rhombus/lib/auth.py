
# LDAP data:
# { 'sys': 'LDAP', 'host': ..., 'DN': ... }

def validate_by_LDAP(username, passwd, scheme):
    import ldap
    l = ldap.open(scheme['host'])
    try:
        l.simple_bind_s(scheme['DN'] % username, passwd)
        return True
    except ldap.INVALID_CREDENTIALS:
        pass
    return False

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

authfunc = {
    'LDAP': validate_by_LDAP,
    'BasicHTTP': validate_by_basichttp
}


# util for adding user automatically
# should return ('lastname', 'firstname')

def inquire_by_LDAP( username, scheme ):
    import ldap
    l = ldap.open(scheme['host'])
    try:
        r = l.search_s( scheme['DN'] % username, ldap.SCOPE_SUBTREE,
                            '(objectclass=*)', [ 'sn', 'givenName'] )
        return ('', '')
    except:
        return ('', '')


def inquire_dummy( username, scheme ):
    return ('', '')


