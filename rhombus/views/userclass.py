
from rhombus.lib.utils import get_dbhandler
from rhombus.views import *


def index(request):
    dbh = get_dbhandler()

    userclasses = dbh.get_userclass()
    userclass_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('UserClass / Domain'), th('Users')
        ],
        tbody()[
            tuple([ tr()[ td('%s' % uc.domain), td('%d' % 1) ] for uc in userclasses ])
        ]
    ]

    return render_to_response('rhombus:templates/generics/page.mako',
            { 'content': str(userclass_table) },
            request = request )

def view(request):
    pass

def edit(request):
    pass

def action(request):
    pass
