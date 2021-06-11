
import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.lib.roles import *
from rhombus.lib.utils import get_dbhandler, random_string, cerr, cout
from rhombus.lib.tags import *
from rhombus.views.generics import not_authorized, error_page

import sqlalchemy.exc
import time

class not_roles(object):

    def __init__(self, *role_list):
        self.not_roles = role_list

msg_0 = 'Please log in first.'

msg_1 = 'Please notify the administrator if you believe that '\
        'you should be able to access this resource.'


class roles(object):

    def __init__(self, *role_list):
        self.allowed = []
        self.disallowed = []
        for role in role_list:
            if isinstance(role, not_roles):
                self.disallowed.extend(role.not_roles)
            else:
                self.allowed.append(role)

    def __call__(self, wrapped):
        if self.allowed or self.disallowed:
            # need to check the roles
            def _view_with_roles(request, **kw):
                if request.user and request.user.has_roles(*self.disallowed):
                    return not_authorized(request, msg_1)
                if PUBLIC in self.allowed and request.user:
                    return wrapped(request, **kw)
                if not request.user:
                    return not_authorized(request, msg_0)
                if not request.user.has_roles(*self.allowed):
                    return not_authorized(request, msg_1)
                return wrapped(request, **kw)
            return _view_with_roles

        else:
            # no roles, just return the function
            return wrapped


class m_roles(roles):

    def __call__(self, wrapped):
        if self.allowed or self.disallowed:
            # need to check the roles
            def _view_with_roles(inst, **kw):
                request = inst.request
                if request.user and request.user.has_roles(*self.disallowed):
                    return not_authorized(request, msg_1)
                if PUBLIC in self.allowed and request.user:
                    return wrapped(inst, **kw)
                if not request.user:
                    return not_authorized(request, msg_0)
                if not request.user.has_roles(*self.allowed):
                    return not_authorized(request, msg_1)
                return wrapped(inst, **kw)
            return _view_with_roles

        else:
            # no roles, just return the function
            return wrapped


class ParseFormError(RuntimeError):

    def __init__(self, msg, field):
        super().__init__(msg)
        self.field = field


class BaseViewer(object):

    template_edit = 'rhombus:templates/generics/formpage.mako'

    # roles that can manage all instances of the object, regardless of the ownership
    managing_roles = [ SYSADM, DATAADM ]

    # roles that can modify instances owned by primary group of a user
    modifying_roles = [] + managing_roles

    # roles that can view instances owned by primary group
    viewing_roles = [ SYSVIEW, DATAVIEW, ] + modifying_roles

    # class to generate new object
    object_class = None

    # function to fetch instance by id
    fetch_func = None

    # routes point to editing & viewing
    edit_route = None
    view_route = None

    # form fields to indicate column: form_field_name
    # eg: {
    #   'groups_id': ('rhombus-user-group_id', list, int),
    #   'data': ('rhombus-user-extdata', json.loads ),
    #   'user_id: ('rhombus-user-user_id', int),
    #   'text': ('rhombus-user-text', )
    #   ]
    form_fields = {}


    # Methods to be defined for each viewer

    def index_helper(self):
        raise NotImplementedError()

    def update_object(self, obj, d):
        """
            update_object should perform the following steps:
            - check permission (eg. if user is authorized to input certain values in the fields, etc)
              and raise AuthorizationError or RuntimeError if necessary
            - add and flush object to database in case for new object
            - handle any integrity error from the database
        """
        raise NotImplementedError()

    def can_modify(self, obj):
        """ return True if obj can be modified by current user
        """
        return False

    def can_view(self, obj):
        """ return True if obj can be viewed by current user
        """
        return False

    def edit_form(self):
        raise NotImplementedError()

    def lookup_helper(self):
        raise NotImplementedError()

    def action_get(self):
        raise NotImplementedError()

    def action_post(self):
        raise NotImplementedError()

    def rpc_helper(self):
        raise NotImplementedError()


    # Internal methods

    def __init__(self, request):
        self.request = request
        self.dbh = get_dbhandler()
        self.obj = None


    @m_roles( PUBLIC )
    def index(self):
        return self.index_helper()


    @m_roles( PUBLIC )
    def view(self):
        return self.view_helper()

    def view_helper(self, render = True):

        rq = self.request
        obj_id = int(rq.matchdict.get('id'))

        obj = self.get_object(obj_id, self.fetch_func)
        eform, jscode = self.edit_form(obj, readonly=True)
        if rq.user.has_roles( * self.managing_roles ) or self.can_modify(obj):
            eform.get('footer').add(
                a('Edit', class_ = 'btn btn-primary offset-md-1',
                    href=rq.route_url(self.edit_route, id=obj.id)) )

        if not render:
            return (eform, jscode)
        return self.render_edit_form(eform, jscode)


    @m_roles( PUBLIC )
    def lookup(self):
        return self.lookup_helper()


    @m_roles( PUBLIC )
    def add(self):
        return self.add_helper()

    def add_helper(self, render=True):

        rq = self.request
        if rq.method == 'POST':

            obj = self.object_class()
            try:
                d = self.parse_form(rq.params)
                self.update_object( obj, self.parse_form(rq.params) )

            except ParseFormError as e:
                err_msg = str(e)
                field = e.field
                eform, jscode = self.edit_form(obj, update_dict = rq.params)
                eform.get(field).add_error(err_msg)
                if not render:
                    return (eform, jscode)
                return self.render_edit_form(eform, jscode)

            return HTTPFound(
                location = self.request.route_url(
                    self.edit_route if rq.params['_method'].endswith('_edit')
                        else self.view_route,
                    id=obj.id))

        dbh = self.dbh
        with dbh.session().no_autoflush:
            eform, jscode = self.edit_form(self.object_class(), create=True)

        if not render:
            return (eform, jscode)
        return self.render_edit_form(eform, jscode)


    @m_roles(PUBLIC)
    def edit(self):
        return self.edit_helper()

    def edit_helper(self, render=True):

        rq = self.request
        obj_id = int(rq.matchdict.get('id'))

        obj = self.get_object(obj_id, self.fetch_func)

        if not (rq.user.has_roles( * self.managing_roles) or self.can_modify(obj)):
            raise RuntimeError('Current user cannot modify this object!')

        if rq.method == 'POST':

            try:
                ok = check_stamp(rq, obj)
                if ok is not True:
                    return ok
                self.update_object(obj, self.parse_form(rq.params))

            except ParseFormError as e:
                err_msg = str(e)
                field = e.field
                eform, jscode = self.edit_form(obj, update_dict = rq.params)
                eform.get(field).add_error(err_msg)
                if not render:
                    return (eform, jscode)
                return self.render_edit_form(eform, jscode)

            return HTTPFound(
                location = self.request.route_url(
                    self.edit_route if rq.params['_method'].endswith('_edit')
                        else self.view_route,
                    id=obj.id))

        eform, jscode = self.edit_form(obj)

        if not render:
            return (eform, jscode)
        return self.render_edit_form(eform, jscode)


    def parse_form(self, form, d=None, fields={}):
        d = d or dict()
        fields = fields or self.form_fields
        d['_stamp_'] = float(form['rhombus-stamp'])

        for key, f in fields.items():
            if f[0] in form:
                if len(f) == 2:
                    try:
                        d[key] = f[1](form[f[0]])
                    except Exception as e:
                        raise ParseFormError(str(e), f[0]) from e
                elif len(f) == 3:
                    if f[1] == list:
                        try:
                            d[key] = [ f[2](x) for x in form.getall(f[0])]
                        except Exception as e:
                            raise ParseFormError(str(e), f[0]) from e
                    else:
                        raise ParseFormError('Error in parsing input', f[0])
                else:
                    d[key] = form[f[0]]

        return d


    def hidden_fields(self, obj):
        request = self.request
        return fieldset (
            input_hidden(name='rhombus-stamp', value='%15f' % obj.stamp.timestamp() if obj.stamp else -1),
            input_hidden(name='rhombus-sesskey', value=generate_sesskey(request.user.id, obj.id)),
            name="rhombus-hidden"
        )


    def render_edit_form(self, eform, jscode):
        return render_to_response(self.template_edit,
            {   'html': eform,
                'code': jscode,
            }, request = self.request
        )


    def get_object(self, obj_id, func):
        rq = self.request
        res = func([obj_id],
                groups = None if rq.user.has_roles( * self.viewing_roles )
                                else rq.user.groups)
        if len(res) == 0:
            raise RuntimeError('Cannot find object! Please check object id!')

        return res[0]

    def set_object(self, obj):
        raise NotImplementedError


def generate_sesskey(user_id, obj_id=None):
    node_id_part = '%08x' % obj_id if obj_id else 'XXXXXXXX'
    return '%08x%s%s' % (user_id, random_string(8), node_id_part)


def check_stamp(request, obj):
    print( "\n>> Time stamp >>", obj.stamp.timestamp(), float(request.params['rhombus-stamp']), "\n")
    if (request.method == 'POST' and
        abs( obj.stamp.timestamp() - float(request.params['rhombus-stamp']) ) > 0.01):
            return error_page(request,
                'Data entry has been modified by %s at %s. Please cancel and re-edit your entry.'
                % (obj.lastuser.login, obj.stamp)
            )
    return True


def form_submit_bar(create=True):
    if create:
        return custom_submit_bar(('Add', 'save'), ('Add and continue editing', 'save_edit')).set_offset(2)
    return custom_submit_bar(('Save', 'save'), ('Save and continue editing', 'save_edit')).set_offset(2)


def select2_lookup(**keywords):
    """ requires minlen, tag, placeholder, parenttag """
    if keywords.get('usetag', True):
        keywords['template'] = "templateSelection: function(data, container) { return data.text.split('|', 1); },"
    else:
        keywords['template'] = ''
    return  '''
  $('#%(tag)s').select2( {
        minimumInputLength: %(minlen)d,
        placeholder: '%(placeholder)s',
        dropdownParent: $("#%(parenttag)s"),
        %(template)s
        ajax: {
            url: "%(url)s",
            dataType: 'json',
            data: function(params) { return { q: params.term }; },
            processResults: function(data, params) { return { results: data }; }
        },
    });
''' % keywords


CLASS = 'class_'

def container(*args, **kwargs):
    if CLASS in kwargs:
        class_ = 'container ' + kwargs[CLASS]
        del kwargs[CLASS]
    else:
        class_ = 'container'
    return div(*args, class_=class_, **kwargs)

def row(*args, **kwargs):
    if CLASS in kwargs:
        class_ = 'row ' + kwargs[CLASS]
        del kwargs[CLASS]
    else:
        class_ = 'row'
    return div(*args, class_=class_, **kwargs)

def button(*args, **kwargs):
    if CLASS in kwargs:
        class_ = 'btn btn-info ' + kwargs[CLASS]
        del kwargs[CLASS]
    else:
        class_ = 'btn btn-info'
    return span(*args, class_=class_, **kwargs)
