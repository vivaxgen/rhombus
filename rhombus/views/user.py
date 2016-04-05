
from rhombus.lib.utils import get_dbhandler
from rhombus.views import *
from rhombus.views.generics import error_page


def index(request):

    dbh = get_dbhandler()

    users = dbh.get_user()
    user_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('Username'), th('Userclass/Domain')
        ],
        tbody()[
            tuple(
                [ tr()[ td('%s' % u.login), td('%s' % u.userclass.domain) ]
                    for u in users ])
        ]
    ]

    return render_to_response('rhombus:templates/generics/page.mako',
            { 'content': str(user_table) },
            request = request )



def view(request):
    raise NotImplementedError()


def edit(request):
    raise NotImplementedError()


def passwd(request):

    user_id = int(request.matchdict.get('id', -1))
    dbh = get_dbhandler()
    user = dbh.get_user(user_id)

    if user.credential == '{X}':
        return error_page(request,
            'ERR: user is using external authentication scheme!')

    if request.POST:
        if user_id != int(request.POST.get('user_id', -1)):
            raise RuntimeError()

        eform = None
        curr_pass = request.POST.get('curr_pass', None)

        if user.verify_credential(curr_pass):
            new_pass = request.POST.get('new_pass', None)
            if new_pass:
                if new_pass == request.POST.get('new_pass2', None):
                    user.set_credential(new_pass)
                else:
                    eform = password_form(user)
                    eform.get('new_pass2').add_error('Password is not verified!')
            else:
                eform = password_form(user)
                eform.get('new_pass').add_error('Please fill the new password!')
        else:
            eform = password_form(user)
            eform.get('curr_pass').add_error('Incorrect password!')

        if eform:
            return render_to_response('rhombus:templates/generics/page.mako',
                { 'content': str(eform) },
                request = request )

        request.session.flash( ('success', 'Successfully changed password for user %s' % user.login) )
        return HTTPFound(location = request.referer or '/')

    eform = password_form(user)

    return render_to_response('rhombus:templates/generics/page.mako',
            { 'content': str(eform) },
            request = request )


def password_form(user):

    eform = form('rhombus.password', method='POST')
    eform.add(
        fieldset()[
            input_hidden('user_id', value = user.id),
            input_text('login', 'Login', value = user.login),
            input_password('curr_pass', 'Current password'),
        ],
        fieldset()[
            input_password('new_pass', 'New password'),
            input_password('new_pass2', 'Verify password')
        ],
        fieldset()[
            submit_bar('Change password')]
    )

    return eform


def action(request):
    pass
