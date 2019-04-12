# package

import sys, os
import argparse
import importlib, importlib.util
from pyramid.paster import get_appsettings, setup_logging
from rhombus.lib.utils import cout, cinfo, cerr, cexit, get_dbhandler
from rhombus.models.core import set_func_userid


PATHS = [ 'rhombus.scripts.' ]
ENVIRON = 'RHOMBUS_CONFIG'
INCLUDES = []
USER = 'USER'
GREET = None
USAGE = None

def set_config( environ=None, paths=None, greet=None, usage=None, dbhandler_class=None, includes=None ):
    global PATHS, ENVIRON, GREET, USAGE

    if environ:
        ENVIRON = environ

    if includes:
        INCLUDES.extend( includes )

    if paths:
        for script_path in paths:
            PATHS.insert(0, script_path)

    if greet:
        GREET = greet

    if usage:
        USAGE = usage

    if dbhandler_class:
        from rhombus.lib.utils import set_dbhandler_class
        set_dbhandler_class( dbhandler_class )

def get_greet():
    return GREET

def get_usage():
    return USAGE


def load_module(command):

    if command.endswith('.py') or '/' in command:
        module_name = 'SCRIPT'

        spec = importlib.util.spec_from_file_location(module_name, command)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    M = None
    for module_path in PATHS:
        try:
            M = importlib.import_module(module_path + command)
            cerr('Importing <%s> from path: %s' % (command, module_path))
            break
        except ImportError as exc:
            pass
    if M is None:
        cexit('Cannot locate script name: %s' % command)

    return M


def execute(command, run_args):

    M = load_module(command)
    if hasattr(M, 'init_argparser'):
        parser = M.init_argparser()
        assert parser, "FATAL ERROR - init_argparser() does not return an instance"
    else:
        cerr('WARN: Using default arg parser!')
        parser = arg_parser()

    args = parser.parse_args(run_args)

    #configfile = args.config or os.environ.get('RHOMBUS_CONFIG')
    #cinfo('Using config file: %s' % configfile)
    #if not configfile:
    #    print('need -c or --config option, or set RHOMBUS_CONFIG environment')
    #    sys.exit(1)

    #print('Connecting to database...')
    #setup_logging( configfile )
    #settings = get_appsettings( configfile )
    #init_db( settings )

    cerr('Running module: %s' % command)
    if M.__name__ == 'SCRIPT':
       settings = setup_settings( args )
       dbh = get_dbhandler( settings )
 
    M.main( args )


def add_script_path( paths ):
    global PATHS
    if type(paths) is list:
        PATHS.add( paths )
    else:
        PATHS.append( paths )


def arg_parser( description = None, parser = None ):

    if not parser:
        parser = argparse.ArgumentParser( description = description, conflict_handler = 'resolve' )

    parser.add_argument('-c', '--config', default=None)
    parser.add_argument('-u', '--user', default=None)

    return parser


def setup_settings( args ):

    cerr('rhombus: setup_settings()')

    configfile = (args.config if args else None) or os.environ.get(ENVIRON)

    if not configfile:
        cexit('need -c or --config option, or set %s environment' % ENVIRON)

    setup_logging( configfile )
    settings = get_appsettings( configfile )

    set_func_userid(userid_func)
    user = (args.user if args else None) or os.environ.get(USER) or None

    if INCLUDES:
        for include_tag in INCLUDES:
            if include_tag not in settings:
                continue
            modules = settings[include_tag].split()
            for module_path in modules:
                cerr('rhombus: importing module: ', module_path)
                M = importlib.import_module(module_path)

    return settings


def userid_func(userid=None):
    return userid
