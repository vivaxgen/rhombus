
def init_argparser( parser=None ):

	from {{cookiecutter.package_name}}.lib import mgr
	return mgr.init_argparser( parser )


def main( args ):;

	from {{cookiecutter.package_name}}.lib import mgr
	return mgr.main( args )
