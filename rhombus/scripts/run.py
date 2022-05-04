
import sys, os
import argparse
import importlib

from sqlalchemy import engine_from_config
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from rhombus.scripts import execute, set_config, get_greet, get_usage
from rhombus.models import init_db
from rhombus.models.handler import DBHandler

def greet():
    print('rhombus-run - Rhombus script utility')


def usage():
    print('Usage:')
    print('\t%s scriptname [options]' % sys.argv[0])
    sys.exit(0)

set_config( environ='RHOMBUS_CONFIG', greet = greet, usage = usage, dbhandler_class = DBHandler )


def main():

    args = sys.argv

    get_greet()()

    if len(args) <= 1:
        get_usage()()
        sys.exit(1)

    scriptname = args[1]

    if '--debug' in args[2:]:
        from ipdb import launch_ipdb_on_exception
        with launch_ipdb_on_exception():
            execute(scriptname, args[2:])

    else:
        execute(scriptname, args[2:])


if __name__ == '__main__':

    print('This script has to be run as rhombus-run')

