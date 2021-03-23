
from rhombus.models import handler as rhombus_handler
from rhombus.lib.utils import cerr, cout

from .setup import setup

from {{cookiecutter.package_name}}.models import post

class DBHandler(rhombus_handler.DBHandler):

    # add additional class references
    Post = post.Post


    def initdb(self, create_table=True, init_data=True, rootpasswd=None):
        """ initialize database """
        super().initdb(create_table, init_data, rootpasswd)
        if init_data:
            from .setup import setup
            setup(self)
            cerr('[{{cookiecutter.package_name}}-rbmgr] Database has been initialized')


    # add additional methods here

    def get_post(self, q):
        """ get single, specific post """
        if type(q) == int:
            return self.Post.get(q, self.session())

    def get_posts(self, query=None):
        """ get multiple posts by query """
        q = self.Post.query( self.session() )

        # do the necessary filtering here

        return q.all()
