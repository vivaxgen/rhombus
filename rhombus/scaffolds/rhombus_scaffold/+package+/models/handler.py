
from rhombus.models import handler as rhombus_handler
from rhombus.lib.utils import cerr, cout

from .setup import setup

class DBHandler(rhombus_handler.DBHandler):

    # add additional class references
    Post = post.Post


    def initdb(self, create_table=True, init_data=True):
        """ initialize database """
        super().initdb(create_table, init_data)
        if init_data:
            from .setup import setup
            setup(self)
            cerr('[rbmgr] Database has been initialized')


    # add additional methods here

    def get_post(self, q):
        if type(q) == int:
            return self.Post.get(q)


