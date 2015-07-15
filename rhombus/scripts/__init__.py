# package

import sys, os
import argparse
import importlib
from pyramid.paster import get_appsettings, setup_logging
from rhombus.lib.utils import cout, cinfo, cerr, cexit


PATHS = [ 'rhombus.scripts.' ]
ENVIRON = 'RHOMBUS_CONFIG'
GREET = None
USAGE = None

def set_config( environ=None, paths=None, greet=None, usage=None, dbhandler_class=None ):
    global PATHS, ENVIRON, GREET, USAGE

    if environ:
        ENVIRON = environ

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


def execute(command, run_args):

    print('paths:', PATHS)

    M = None
    for module_path in PATHS:
        try:
            print(module_path)
            M = importlib.import_module(module_path + command)
            break
        except ImportError as exc:
            pass
    if M is None:
        cexit('Cannot locate script name: %s' % command)

    print(M)

    if hasattr(M, 'init_argparser'):
        parser = M.init_argparser()
        assert parser, "FATAL ERROR - init_argparser() does not return an instance"
    else:
        print('Use default arg parser!')
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

    M.main( args )


def add_script_path( paths ):
    global PATHS
    if type(paths) is list:
        PATHS.add( paths )
    else:
        PATHS.append( paths )


def arg_parser( description = None, parser = None ):

    if not parser:
        parser = argparse.ArgumenParser( description = description )

    parser.add_argument('-c', '--config', default=None)

    return parser


def setup_settings( args ):

    configfile = args.config or os.environ.get(ENVIRON)

    if not configfile:
        cexit('need -c or --config option, or set %s environment' % ENVIRON)

    setup_logging( configfile )
    settings = get_appsettings( configfile )
    return settings

