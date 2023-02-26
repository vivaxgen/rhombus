
from rhombus.lib.modals import popup, modal_delete, modal_error

from rhombus.lib.roles import PUBLIC, SYSADM, SYSVIEW, EK_VIEW, EK_CREATE, EK_MODIFY, EK_DELETE
from rhombus.lib.tags import (div, table, thead, tbody, th, tr, td, literal, selection_bar, br, ul, li, a, i,
                              form, POST, GET, fieldset, input_text, input_hidden, input_select, input_password,
                              submit_bar, h3, p, input_textarea, h2)
from rhombus.views import get_dbhandler, roles, render_to_response, HTTPFound, Response
from rhombus.views.generics import error_page


@roles(SYSADM, SYSVIEW, EK_VIEW)
def index(request):
    """ list all non-member/root EnumKey (EK) """

    dbh = get_dbhandler()
    eks = dbh.EK.query(dbh.session()).filter(dbh.EK.member_of_id == None)

    html, code = format_ektable(eks, request)

    html = div((h2('Enumerated Key'))).add(html)

    return render_to_response('rhombus:templates/generics/page.mako', {
        'html': html,
        'code': code
    }, request=request)


@roles(SYSADM, SYSVIEW, EK_VIEW)
def view(request):
    """ view a EnumKey along with its members """
    ek_id = int(request.matchdict.get('id', -1))
    dbh = get_dbhandler()
    ek = dbh.EK.get(ek_id, dbh.session())
    if not ek:
        return error_page(request)

    eform = edit_form(ek, dbh, request, readonly=True)
    html, code = format_ektable(ek.members, request, ek)

    html = div((h2('Enumerated Key'))).add(eform, br, html)

    return render_to_response('rhombus:templates/generics/page.mako', {
        'html': html,
        'code': code
    }, request=request)


@roles(SYSADM, SYSVIEW, EK_MODIFY, EK_CREATE)
def edit(request):
    """ edit a EnumKey """

    dbh = get_dbhandler()
    ek_id = int(request.matchdict.get('id', -1))
    if ek_id < 0:
        return error_page(request)
    if ek_id == 0:
        ek = dbh.EK()
        ek.id = 0
        ek.member_of_id = int(request.params.get('member_of_id', 0))
    else:
        ek = dbh.EK.get(ek_id, dbh.session())

    eform = edit_form(ek, dbh, request)

    return render_to_response('rhombus:templates/ek/edit.mako', {
        'ek': ek,
        'form': eform
    }, request=request)


@roles(SYSADM, EK_CREATE, EK_MODIFY)
def save(request):
    """ save a EnumKey """
    ek_id = int(request.matchdict.get('id', -1))
    dbh = get_dbhandler()
    ek = parse_form(request.POST, dbh)
    if ek_id == 0:
        session = dbh.session()
        session.add(ek)
        session.flush()
        db_ek = ek
    else:
        db_ek = dbh.EK.get(ek_id, dbh.session())
        if not db_ek:
            return error_page(request)
        db_ek.update(ek)

    if ek_id != 0:
        location = request.route_url('rhombus.ek-view', id=ek_id)
    elif ek.member_of_id:
        location = request.route_url('rhombus.ek-view', id=ek.member_of_id)
    else:
        location = request.route_url('rhombus.ek-view', id=ek.id)

    return HTTPFound(location=location)


def edit_form(ek, dbh, request, readonly=False):

    from rhombus.lib import tags as t

    eform = t.form(name='rhombus.ek', method=t.POST, readonly=readonly,
                   action=request.route_url('rhombus.ek-save', id=ek.id or 0))
    eform.add(
        t.fieldset(
            t.input_hidden('ek.id', value=ek.id or 0),
            t.input_hidden('ek.member_of_id', value=ek.member_of_id),
            t.input_text('ek.key', 'Enum Key', value=ek.key),
            t.input_text('ek.desc', 'Description', ek.desc),
            t.checkboxes('ek.options', 'Option', [('ek.syskey', 'System key', ek.syskey)]),
            t.input_textarea('ek.data', 'Aux Data', ek.data or ''),
        ),
        t.fieldset(
            t.submit_bar() if not readonly else a('Edit', class_='btn btn-primary offset-md-3',
                                                  href=request.route_url('rhombus.ek-edit',
                                                                         id=ek.id))
        )
    )
    return eform


def parse_form(d, dbh):
    """ parse form and save it to an EnumKey instance """
    ek = dbh.EK()
    ek.id = int(d.get('id', 0)) or None
    ek.key = d.get('ek.key')
    ek.desc = d.get('ek.desc')
    ek.syskey = True if d.get('ek.syskey', 0) else False
    ek.data = d.get('ek.data').encode('UTF-8') or None
    ek.member_of_id = int(d.get('ek.member_of_id', 0)) or None
    return ek


@roles(SYSADM)
def lookup(request):
    """ return JSON for autocomplete """
    q = request.params.get('q')
    g = request.params.get('g', '')
    dbh = get_dbhandler()
    g_key = dbh.get_ekey(g)

    if not g_key:
        return error_page(request, "Parent EK not found!")

    if not q:
        return error_page(request, "Please provide the query as q.")

    q = '%' + q.lower() + '%'

    ekeys = dbh.EK.query(dbh.session()).filter(dbh.EK.key.ilike(q),
                                               dbh.EK.member_of_id == g_key.id)

    # formating for select2 consumption

    result = [
        {'id': k.id, 'text': '%s [ %s ]' % (k.key, k.desc)}
        for k in ekeys]

    return result


@roles(SYSADM, EK_MODIFY, EK_DELETE)
def action(request):

    dbh = get_dbhandler()
    EK = dbh.EK

    if not request.POST:
        return error_page()

    method = request.POST.get('_method')

    if method == 'delete':
        ids = request.POST.getall('ek-ids')
        eks = list(EK.query(dbh.session()).filter(EK.id.in_(ids)))

        if len(eks) == 0:
            return Response(modal_error(content="Please select Enumerated Key(s) to be removed"))

        # return Response('Delete Enumerated Keys: ' + str(request.POST))
        # return Response(modal_delete % ''.join( '<li>%s</li>' % x.key for x in eks ))
        return Response(
            modal_delete(
                title='Deleting EKey(s)',
                content=literal(
                    'You are going to delete the following key(s):'
                    '<ul>' +
                    ''.join('<li>%s</li>' % x.key for x in eks) +
                    '</ul>'
                ),
                request=request
            ),
            request=request
        )

    elif method == 'delete/confirm':
        ids = request.POST.getall('ek-ids')

        count = 0
        for ek_id in ids:
            EK.delete(ek_id, dbh.session())
            count += 1

        request.session.flash(('success', 'Successfully removed %d Enumerated Keys' % count))

        return HTTPFound(location=request.referer)

    return Response(str(request.POST))


def format_ektable(eks, request, ek=None):

    ek_table = table(class_='table table-condensed table-striped')[
        thead()[
            th('', style='width: 2em'), th('Key'), th('Description')
        ],
        tbody()[
            tuple([
                tr()[
                    td(literal('<input type="checkbox" name="ek-ids" value="%d">' % ek.id)),
                    td(a('%s' % ek.key, href=request.route_url('rhombus.ek-view', id=ek.id))),
                    td('%s' % ek.desc)
                ] for ek in eks
            ])
        ]
    ]

    add_button = ('Add key',
                  request.route_url('rhombus.ek-edit', id=0,
                                    _query={'member_of_id': ek.id} if ek else {}))

    bar = selection_bar('ek-ids', action=request.route_url('rhombus.ek-action'),
                        add=add_button)

    return bar.render(ek_table)


# EOF
