

from rhombus.lib.utils import cerr, get_dbhandler
from rhombus.scripts import setup_settings, arg_parser, run

import sys


def greet():
    cerr('rhombus-shell - shell for Rhombus')


def usage():
    greet()
    cerr('usage:')
    cerr('\t%s scriptname [options]' % sys.argv[0])
    sys.exit(0)


def main():
    greet()

    # preparing everything
    p = arg_parser('rhombus-shell')
    args = p.parse_args(sys.argv[1:])

    settings = setup_settings( args )
    dbh = get_dbhandler(settings)

    from IPython import embed
    import transaction
    embed()

