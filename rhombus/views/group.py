
from rhombus.views import *

from rhombus.models.user import Group


@roles( PUBLIC )
def index(request):
    """ list groups """

    dbh = get_dbhandler()
    groups = Group.query(dbh.session()).order_by( Group.name )

    t = table(class_='table table-condensed table-striped')
    t.add( thead()[
            tr()[ th(), th('Group Name'), th('Members') ]
        ])

    tb = tbody()
    for grp in groups:
        tb.add( tr()[ td(), td(grp.name), td(len(grp.users)) ] )

    t.add( tb )



    return render_to_response('rhombus:templates/group/index.mako',
                { 'groups': groups }, request=request )
    raise NotImplementedError


def view(request):
    raise NotImplementedError


def edit(request):
    raise NotImplementedError


def save(request):
    raise NotImplementedError


def action(requst):
    raise NotImplementedError


def lookup(request):
    raise NotImplementedError
