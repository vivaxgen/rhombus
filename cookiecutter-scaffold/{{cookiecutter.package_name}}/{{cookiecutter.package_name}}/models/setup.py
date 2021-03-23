
from {{cookiecutter.package_name}}.models import *

def setup( dbh ):

    dbh.EK.bulk_update( ek_initlist, dbsession=dbh.session() )


# add additional initial data here


ek_initlist = [
    (   '@SYSNAME', 'System names',
        [
            ( '{{cookiecutter.package_name}}'.upper(), '{{cookiecutter.package_name}}' ),
        ]
    ),
    (   '@POSTTYPE', 'Post types',
        [
            ( 'Article', 'article'),
            ( 'News', 'news')
        ]
    ),
]
