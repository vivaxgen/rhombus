# rbmgr.py


def init_argparser(parser=None):

    from rhombus.lib import mgr
    return mgr.init_argparser(parser)


def main(args):

    from rhombus.lib import mgr

    if args.debug:
        from ipdb import launch_ipdb_on_exception
        with launch_ipdb_on_exception():
            return mgr.main(args)

    else:
        return mgr.main(args)

# EOF
