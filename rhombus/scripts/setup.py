
import sys, os
import transaction


from pyramid.paster import (
    get_appsettings,
    setup_logging
    )

from rhombus.models import init_db
from rhombus.models.setup import setup_db
from rhombus.models.user import UserClass, Group
from rhombus.models.ek import EK
from rhombus.lib.roles import *


def usage(args):
    cmd = os.path.basename(args[0])
    print('usage: %s configfile' % cmd)
    sys.exit(1)


def setup(args):

    if len(args) > 1:
        configfile = args[1]
    else:
        configfile = os.environ.get('PYRAMID_CONFIG', None)

    if not configfile:
        usage()

    setup_logging( configfile )
    settings = get_appsettings( configfile )
    init_db( settings, create_table = True )

    setup_db( populate_db )


def populate_db( dbsession, initial_groups=None, initial_userclass=None ):

    if initial_groups:
        Group.bulk_insert( initial_groups, dbsession=dbsession )
    if initial_userclass:
        UserClass.bulk_insert( initial_userclass, dbsession=dbsession )


def main(args=sys.argv):
    setup(args)
