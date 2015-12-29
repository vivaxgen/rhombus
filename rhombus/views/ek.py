
from rhombus.views import *


@roles( PUBLIC )
def index(request):
    """ list all non-member/root EnumKey (EK) """

    dbh = get_dbhandler()
    eks = dbh.EK.query(dbh.session()).filter( dbh.EK.member_of_id == None )
    return render_to_response( 'rhombus:templates/ek/index.mako',
                    { 'eks': eks }, request = request )



@roles( SYSADM, SYSVIEW, EK_VIEW )
def view(request):
    """ view a EnumKey along with its members """
    ek_id = int(request.matchdict.get('id', -1))
    dbh = get_dbhandler()
    ek = dbh.EK.get(ek_id)
    if not ek:
        return error_page()

    return render_to_response('rhombus:templates/ek/view.mako',
            { 'ek': ek }, request = request )




@roles( SYSADM, SYSVIEW, EK_MODIFY, EK_CREATE )
def edit(request):
    """ edit a EnumKey """

    dbh = get_dbhandler()
    ek_id = int(request.matchdict.get('id', -1))
    if ek_id < 0:
        return error_page()
    if ek_id == 0:
        ek = dbh.EK()
        ek.id = 0
        ek.member_of_id = int(request.params.get('member_of_id', 0))
    else:
        ek = dbh.EK.get(ek_id)

    eform = edit_form(ek, dbh, request)

    return render_to_response('rhombus:templates/ek/edit.mako',
            { 'ek': ek, 'form': eform }, request = request )


@roles( SYSADM, EK_CREATE, EK_MODIFY )
def save(request):
    """ save a EnumKey """
    ek_id = int(request.matchdict.get('id', -1))
    dbh = get_dbhandler()
    ek = parse_form(request.POST, dbh)
    if ek_id == 0:
        session = dbh.session()
        session.add( ek )
        session.flush()
        db_ek = ek
    else:
        db_ek = EK.get(ek_id)
        if not db_ek:
            return error_page()
        db_ek.update( ek )

    if ek_id != 0:
        location = request.referer or request.route_url('rhombus.ek-view', id=ek_id)
    elif ek.member_of_id:
        location = request.route_url('rhombus.ek-view', id = ek.member_of_id)
    else:
        location = request.route_url('rhombus.ek-view', id = ek.id)

    return HTTPFound( location = location )


def edit_form( ek, dbh, request, static=False ):

    from rhombus.lib import tags as t

    form = t.form(name='rhombus.ek', method=t.POST,
                    action=request.route_url('rhombus.ek-save', id=ek.id or 0))
    form.add(
        t.fieldset(
            t.input_hidden('ek.id', value=ek.id or 0),
            t.input_hidden('ek.member_of_id', value=ek.member_of_id),
            t.input_text('ek.key', 'Enum Key', value=ek.key),
            t.input_text('ek.desc', 'Description', ek.desc),
            t.checkboxes('ek.options', 'Option',
                    [ ('ek.syskey', 'System key', ek.syskey) ]),
            t.input_textarea('ek.data', 'Aux Data', ek.data or ''),
        ),
        t.fieldset(
            t.submit_bar()
        )
    )
    return form


def parse_form( d, dbh ):
    """ parse form and save it to an EnumKey instance """
    ek = dbh.EK()
    ek.id = int(d.get('id', 0)) or None
    ek.key = d.get('ek.key')
    ek.desc = d.get('ek.desc')
    ek.syskey = True if d.get('ek.syskey', 0) else False
    ek.data = d.get('ek.data').encode('UTF-8') or None
    ek.member_of_id = int(d.get('ek.member_of_id', 0)) or None
    return ek


def lookup(request):
    raise NotImplementedError


@roles( SYSADM, EK_MODIFY, EK_DELETE )
def action(request):

    if not request.POST:
        return error_page()

    method = request.POST.get('_method')

    if method == 'delete':
        ids = request.POST.getall('ek-ids')
        eks = list( EK.query().filter( EK.id.in_( ids ) ) )

        if len(eks) == 0:
            return Response(modal_error)

        #return Response('Delete Enumerated Keys: ' + str(request.POST))
        return Response(modal_delete % ''.join( '<li>%s</li>' % x.key for x in eks ))

    elif method == 'delete/confirm':
        ids = request.POST.getall('ek-ids')

        count = 0
        for ek_id in ids:
            EK.delete( ek_id )
            count += 1

        request.session.flash( ('success', 'Successfully removed %d Enumerated Keys' % count) )

        return HTTPFound(location = request.referer)

    return Response(str(request.POST))


modal_delete = '''
<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
    <h3 id="myModalLabel">Deleting Enumerated Keys</h3>
</div>
<div class="modal-body">
    <p>You are going to delete the following EK(s):
        <ul>
        %s
        </ul>
    </p>
</div>
<div class="modal-footer">
    <button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button>
    <button class="btn btn-danger" type="submit" name="_method" value="delete/confirm">Confirm Delete</button>
</div>
'''

modal_error = '''
<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
    <h3 id="myModalLabel">Error</h3>
</div>
<div class="modal-body">
    <p>Please select Enumerated Key(s) to be removed</p>
</div>
<div class="modal-footer">
    <button class="btn" data-dismiss="modal" aria-hidden="true">Close</button>
</div>
'''

