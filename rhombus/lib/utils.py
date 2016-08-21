import sys, base64, os, math, contextlib, shutil

def cout(s, nl=True, flush=False):
    sys.stdout.write(s)
    if nl: sys.stdout.write('\n')
    if flush: sys.stdout.flush()

def cerr(s, nl=True, flush=False):
    sys.stderr.write(s)
    if nl: sys.stderr.write('\n')
    if flush: sys.stderr.flush()

def cexit(s, code=1):
    cerr(s)
    sys.exit(code)

cinfo = cout

# general utils

random_string = lambda n: base64.b64encode(os.urandom(int(math.ceil(0.75*n))), b'-_')[:n].decode('UTF-8')

def silent_remove( path ):
    try:
        os.remove( path )
    except FileNotFoundError:
        pass

def silent_rmdir( path ):
    shutil.rmtree(path, ignore_errors = True)


# dbhandler

# global var
_DBHANDLER_ = None
_DBHANDLER_CLASS_ = None

def get_dbhandler( settings = None, tag = 'sqlalchemy.', initial=False):
    """ get global dbhandler """

    global _DBHANDLER_, _DBHANDLER_CLASS_

    # get the config file
    if _DBHANDLER_ is None:
        if settings is None:
            cerr('FATAL ERROR - get_dbhandler() called first time without settings')
            sys.exit(1)
        if _DBHANDLER_CLASS_ is None:
            cerr('FATAL ERROR - call set_dbhandler_class() before calling get_dbhandler()')
            sys.exit(1)
        _DBHANDLER_ = _DBHANDLER_CLASS_( settings, tag, initial )

    elif settings is not None:
        cerr('FATAL ERROR - get_dbhandler() must not have settings for consecutive calls')
        sys.exit(1)

    return _DBHANDLER_


def get_dbhandler_notsafe():
    global _DBHANDLER_
    return _DBHANDLER_


def set_dbhandler_class( class_ ):
    global _DBHANDLER_CLASS_
    cerr('Setting dbhandler class to %s' % str(class_))
    _DBHANDLER_CLASS_ = class_


def generic_userid_func():
    global _DBHANDLER_
    return _DBHANDLER_.session().user.id

