# rbmgr.py


def init_argparser( parser = None ):

    from rhombus.lib import mgr
    return mgr.init_argparser( parser )


def main( args ):

    from rhombus.lib import mgr
    return mgr.main( args )
