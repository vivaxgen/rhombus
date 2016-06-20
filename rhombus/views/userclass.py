
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
            tuple([ tr()[
                        td('%s' % uc.domain),
                        td(a('%d' % uc.users.count(), href=request.route_url('rhombus.userclass-view', id=uc.id)) )
                    ] for uc in userclasses ])
        ]
    ]

    return render_to_response('rhombus:templates/generics/page.mako',
            { 'content': str(userclass_table) },
            request = request )

def view(request):

    dbh = get_dbhandler()
    userclass = dbh.get_userclass( int(request.matchdict['id']) )

    html = div( div(h3('Userclass: %s' % userclass.domain)))

    user_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('Login'), th('Name'), th('Primary group')
        ],
        tbody()[
            tuple([ tr()[
                        td(a(u.login, href=request.route_url('rhombus.user-view', id=u.id))),
                        td(u.fullname()),
                        td(a(u.primarygroup.name,
                            href=request.route_url('rhombus.group-view', id=u.primarygroup_id))),
                    ] for u in userclass.users ])
        ]
    ]

    html.add(user_table)

    return render_to_response('rhombus:templates/generics/page.mako',
            { 'content': str(html) },
            request = request )


def edit(request):
    raise NotImplementedError()

def action(request):
    raise NotImplementedError()
