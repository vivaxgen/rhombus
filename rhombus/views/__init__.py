
import logging
from pyramid.response import Response, FileIter
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.lib.roles import PUBLIC, SYSADM, SYSVIEW, DATAADM, DATAVIEW
from rhombus.lib.utils import get_dbhandler, random_string, cerr, cout
from rhombus.lib.fileutils import save_file
from rhombus.views.generics import not_authorized, error_page
from rhombus.models.fileattach import FileAttachment
import rhombus.lib.tags as t

import sqlalchemy.exc
import yaml
import mimetypes
import time
import pathlib

log = logging.getLogger(__name__)


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
    managing_roles = [SYSADM, DATAADM]

    # roles that can modify instances owned by primary group of a user
    modifying_roles = [] + managing_roles

    # roles that can view instances owned by primary group
    viewing_roles = [SYSVIEW, DATAVIEW, ] + modifying_roles

    # roles that can access all urls
    accessing_roles = [PUBLIC]

    # class to generate new object
    object_class = None

    # function to fetch instance by id
    fetch_func = None

    # routes point to editing & viewing
    edit_route = None
    view_route = None
    attachment_route = None

    # form fields to indicate column: form_field_name
    # eg: {
    #   'groups_id': ('rhombus-user-group_id', list, int),
    #   'data': ('rhombus-user-extdata', json.loads ),
    #   'user_id: ('rhombus-user-user_id', int),
    #   'text': ('rhombus-user-text', )
    #   }
    # add the following symbols after field name for more control of the fields
    #   ? - optional value, where the database column is nullable
    #   ! - mandatory value
    #   @ - a file attachment field
    form_fields = {}

    # additional functions to be invoked

    # preupdate and postupdate objects, function signature is func(viewer, object, dict)
    __preupdate_funcs__ = []
    __postupdate_funcs__ = []

    # postedit form, function signature is:
    #   eform, js = func(viewer, obj, eform, js, create, readonly, update_dict)
    __posteditform_funcs__ = []

    # Methods to be defined for each viewer

    def index_helper(self):
        raise NotImplementedError()

    def update_object(self, obj, d):
        """
            update_object should perform the following steps:
            - check permission (eg. if user is authorized to input certain values in the fields, etc)
              and raise AuthorizationError or RuntimeError if necessary
            - perform self.preupdate_object(obj, d)
            - add (check by obj.id is None) to database in case for new object
            - perform self.postupdate_object(obj, d)
            - flush object to database
            - handle any integrity error from the database
        """
        raise NotImplementedError()

    def can_manage(self, obj=None):
        return self.request.user.has_roles(* self.managing_roles)

    def can_modify(self, obj=None):
        """ return True if obj can be modified by current user
        """
        if self.can_manage():
            return True
        obj = obj or self.obj
        if obj is not None and obj.can_modify(self.request.user):
            # return based on the object permission
            return True
        return False

    def can_view(self, obj):
        """ return True if obj can be viewed by current user
        """
        return False

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):
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

        # request from the web
        self.request = request

        # database handler
        self.dbh = get_dbhandler()

        # current object instance
        self.obj = None

        # temporary variables to be used by this instance
        self.vars = {}

    @m_roles(* accessing_roles)
    def index(self):
        return self.index_helper()

    @m_roles(* accessing_roles)
    def view(self):
        self.obj = self.get_object()
        return self.view_helper()

    def view_helper(self, render=True):

        rq = self.request
        obj = self.obj or self.get_object()
        eform, jscode = self.generate_edit_form(obj, readonly=True)
        if rq.user.has_roles(* self.managing_roles) or self.can_modify(obj):
            eform.get('footer').add(
                t.a('Edit', class_='btn btn-primary offset-md-2',
                    href=rq.route_url(self.edit_route, id=obj.id)))

        if not type(eform) is t.div:
            eform = t.div(eform)
        html, jscode = self.view_extender(eform, jscode)

        if not render:
            return (html, jscode)
        return self.render_edit_form(html, jscode)

    def view_extender(self, html, jscode):
        return html, jscode

    @m_roles(* accessing_roles)
    def lookup(self):
        return self.lookup_helper()

    @m_roles(* accessing_roles)
    def action(self):

        _m = self.request.method

        if _m == 'GET':
            return self.action_get()

        elif _m == 'POST':
            return self.action_post()

        elif _m == 'PUT':
            return self.action_put()

        elif _m == 'DELETE':
            return self.action_delete()

        return error_page(self.request, 'HTTP method not implemented!')

    @m_roles(* accessing_roles)
    def add(self):
        return self.add_helper()

    def add_helper(self, render=True):

        if self.object_class is None:
            raise TypeError(f'{self.__class__}.object_class has not been initialized.')

        rq = self.request
        if rq.method == 'POST':

            self.obj = obj = self.object_class()
            try:
                self.update_object(obj, self.parse_form(rq.params))

                # with addition, permission check is performed after 

            except AssertionError:
                raise

            except ParseFormError as e:
                err_msg = str(e)
                field = e.field
                eform, jscode = self.generate_edit_form(obj, update_dict=rq.params,
                                                        create=True if obj.id is None else False)
                eform.get(field).add_error(err_msg)
                # for debugging purposes, add debug text to form
                eform.add(t.literal(f'<!--\n[[EXC: ParseFormError at: {field} with: {err_msg}]]\n-->'))
                if not render:
                    return (eform, jscode)
                return self.render_edit_form(eform, jscode)

            except sqlalchemy.exc.DataError as err:
                self.dbh.session().rollback()
                detail = err.args[0]

                raise RuntimeError(detail)

            return HTTPFound(
                location=self.request.route_url(
                    self.edit_route if rq.params['_method'].endswith('_edit')
                    else self.view_route,
                    id=obj.id))

        dbh = self.dbh
        with dbh.session().no_autoflush:
            eform, jscode = self.generate_edit_form(self.object_class(), create=True)

        if not render:
            return (eform, jscode)
        return self.render_edit_form(eform, jscode)

    @m_roles(* accessing_roles)
    def edit(self):
        self.obj = self.get_object()
        return self.edit_helper()

    def edit_helper(self, render=True):

        rq = self.request
        obj = self.obj or self.get_object()

        # with editing, permission check is performed before any processing
        if not (rq.user.has_roles(* self.managing_roles) or self.can_modify(obj)):
            raise RuntimeError('Current user cannot modify this object!')

        if rq.method == 'POST':

            try:
                ok = check_stamp(rq, obj)
                if ok is not True:
                    return ok
                self.update_object(obj, self.parse_form(rq.params))

            except AssertionError:
                raise

            except ParseFormError as e:
                err_msg = str(e)
                field = e.field
                eform, jscode = self.generate_edit_form(obj, update_dict=rq.params)
                eform.get(field).add_error(err_msg)
                if not render:
                    return (eform, jscode)
                return self.render_edit_form(eform, jscode)

            except sqlalchemy.exc.DataError as err:
                self.dbh.session().rollback()
                detail = err.args[0]

                raise RuntimeError(detail)

            return HTTPFound(
                location=self.request.route_url(
                    self.edit_route if rq.params['_method'].endswith('_edit')
                    else self.view_route,
                    id=obj.id))

        eform, jscode = self.generate_edit_form(obj)

        if not render:
            return (eform, jscode)
        return self.render_edit_form(eform, jscode)

    #
    # attachment() is used to serve file attachment

    @m_roles(* accessing_roles)
    def attachment(self):

        rq = self.request
        fieldname = rq.matchdict.get('fieldname')
        obj = self.get_object()
        file_instance = getattr(obj, fieldname)
        content_encoding = mimetypes.guess_type(file_instance.filename)[1]
        return Response(app_iter=FileIter(file_instance.fp()),
                        content_type=file_instance.mimetype, content_encoding=content_encoding,
                        content_disposition=f'inline; filename="{file_instance.filename}"',
                        request=rq)

    def attachment_link(self, obj, attrname):
        if not (attachment := getattr(obj, attrname)):
            return ''
        return t.div(t.a(attachment.filename,
                         href=self.request.route_url(self.attachment_route, id=obj.id,
                                                     fieldname=attrname)),
                     class_='col-md-4 d-flex align-self-center',
                     )

    #
    # fileupload() to facilitate uploading file
    # the sent form should contain sesskey

    @m_roles(* accessing_roles)
    def fileupload(self):

        request = self.request

        sesskey = request.matchdict.get('sesskey')
        user_id, instance_id = tokenize_sesskey(sesskey)
        if user_id != request.user.id:
            raise RuntimeError('Invalid session key!')

        filestorage = request.POST.get('files[]')
        filename = pathlib.Path(filestorage.filename).name

        tmp_dir = request.registry.settings['cmsfix.tmpdir']
        dest_path = tmp_dir + '%s.payload' % sesskey

        size, total = save_file(dest_path, filestorage, request)

        if size == total:
            dbh = get_dbhandler()
            file_mimetype = mimetypes.guess_type(filename)
            try:
                if not file_mimetype[0]:
                    mimetype_id = dbh.EK._id('application/unknown', grp='@MIMETYPE')
                else:
                    mimetype_id = dbh.EK._id(file_mimetype[0], grp='@MIMETYPE')
            except KeyError:
                mimetype_id = dbh.EK._id('application/unknown', grp='@MIMETYPE')

            return {'basename': filename, 'size': size, 'mimetype_id': mimetype_id}

        return {}

    # parse_form() is uset to parse html form and convert the value as necessary
    # to a dictionary

    def parse_form(self, form, d=None, fields={}):
        """ fields format:
            key: (name, modifier1, modifier2)

            if modifier1 is list, will convert each item using modifier2

        """
        d = d or dict()
        fields = fields or self.form_fields
        d['_stamp_'] = float(form['rhombus-stamp'])

        for key, f in fields.items():

            nullable = False
            required = False
            attachment_field = False
            if key.endswith('?'):
                # value is optional
                key = key[:-1]
                nullable = True
            elif key.endswith('*') or key.endswith('!'):
                # value must exist
                key = key[:-1]
                required = True
            elif key.endswith('@'):
                # this is a file attachment field which will be accompanied by
                # a check-box field of 'tag-XCB'
                key = key[:-1]
                if form.get(f[0] + '-XCB', '') == 'on':
                    attachment_field = None

            if (name := f[0]) in form:
                value = form[name].strip() if type(form[name]) == str else form[name]
                if nullable and value == '':
                    continue
                if required and value == '':
                    raise ParseFormError('This field is mandatory!', name)
                if len(f) == 2:
                    try:
                        val = f[1](value)
                        if nullable and (val is None or val == ''):
                            continue
                        d[key] = val
                    except AssertionError:
                        raise
                    except Exception as e:
                        raise ParseFormError(str(e), name) from e
                elif len(f) == 3:
                    if f[1] == list:
                        try:
                            d[key] = [f[2](x) for x in form.getall(name)]
                        except Exception as e:
                            raise ParseFormError(str(e), name) from e
                    else:
                        raise ParseFormError('Error in parsing input', name)
                else:
                    if value == b'' and attachment_field is None:
                        d[key] = None
                        continue
                    d[key] = value
            elif required:
                raise ParseFormError('You must fill this field!', name)

        return d

    def hidden_fields(self, obj, stamp=None, sesskey=None):
        request = self.request
        return t.fieldset(
            t.input_hidden(name='rhombus-stamp',
                           value=stamp or ('%15f' % obj.stamp.timestamp() if obj.stamp else -1)),
            t.input_hidden(name='rhombus-sesskey',
                           value=sesskey or generate_sesskey(request.user.id, obj.id)),
            name="rhombus-hidden"
        )

    def generate_edit_form(self, obj=None, create=False, readonly=False, update_dict=None):
        eform, js = self.edit_form(obj, create, readonly, update_dict)
        for f in self.__posteditform_funcs__:
            eform, js = f(self, obj, eform, js, create, readonly, update_dict)
        return eform, js

    def render_edit_form(self, eform, jscode):
        return render_to_response(self.template_edit, {
            'html': eform,
            'code': jscode,
        }, request=self.request)

    def get_object(self, obj_id=None, func=None, tag='id'):
        """get the object instance, ensuring that the current user has the necessary authorization"""
        rq = self.request
        obj_id = obj_id or int(self.request.matchdict.get(tag))
        func = func or self.fetch_func
        if func is None and self.fetch_func is None:
            raise TypeError(f'{self.__class__}.fetch_func has not been initialized.')
        res = func([obj_id],
                   groups=None if rq.user.has_roles(* self.viewing_roles)
                   else rq.user.groups,
                   user=rq.user)
        if len(res) == 0:
            raise RuntimeError('Either the object does not exist or you do not have '
                               'the authorization to access the object!')

        self.obj = res[0]
        return self.obj

    def set_object(self, obj):
        raise NotImplementedError

    def ffn(self, ident):
        """ ffn - formm field name """
        field_spec = self.form_fields[ident]
        if type(field_spec) is not tuple:
            raise ValueError(f'form field: {ident} is not a tuple!')
        return field_spec[0]

    def preupdate_object(self, obj, d):
        """ perform necessary stuff before updating object """
        for f in self.__preupdate_funcs__:
            f(self, obj, d)

    def postupdate_object(self, obj, d):
        """ perform necessary stuff after updating object """
        for f in self.__postupdate_funcs__:
            f(self, obj, d)


# stamp handling

def check_stamp(request, obj):
    print("\n>> Time stamp >>", obj.stamp.timestamp(), float(request.params['rhombus-stamp']), "\n")
    if (request.method == 'POST' and abs(obj.stamp.timestamp() - float(request.params['rhombus-stamp'])) > 0.01):
        return error_page(request,
                          f'Data entry has been modified by {obj.lastuser.login} at {obj.stamp}.'
                          f' Please cancel, reload and re-edit your entry.')
    return True


# session key handling

def generate_sesskey(user_id, obj_id=None):
    """ universal url-safe and filesystem-safe session key generator based on user_id & obj_id """
    obj_id_part = '%08x' % obj_id if obj_id else 'XXXXXXXX'
    return '%08x%s%s' % (user_id, random_string(16), obj_id_part)


def tokenize_sesskey(sesskey):
    """ returning usee_id and node_id part """
    # check sanity
    if '/' in sesskey or '\\' in sesskey:
        raise ValueError('invalid session key')
    user_id = int(sesskey[0:8], 16)
    obj_id_part = sesskey[24:32]
    if obj_id_part == 'XXXXXXXX':
        obj_id = None
    else:
        obj_id = int(obj_id_part, 16)
    return user_id, obj_id


# response generator

def fileinstance_to_response(file_instance=None, fp=None, filename=None,
                             mimetype=None, content_encoding=None, request=None):
    fp = fp or file_instance.fp()
    filename = filename or file_instance.filename
    mimetype = mimetype or file_instance.mimetype
    content_encoding = content_encoding or mimetypes.guess_type(file_instance.filename)[1]
    return Response(app_iter=FileIter(fp),
                    content_type=mimetype,
                    content_encoding=content_encoding,
                    content_disposition=f'inline; filename="{filename}"',
                    request=request)


# parser helpers

def yaml_load(data):
    return yaml.load(data, Loader=yaml.Loader)


def boolean_checkbox(value):
    if value.lower() == 'on':
        return True
    return False


def form_submit_bar(create=True):
    if create:
        return t.custom_submit_bar(('Add', 'save'), ('Add and continue editing', 'save_edit')).set_offset(2)
    return t.custom_submit_bar(('Save', 'save'), ('Save and continue editing', 'save_edit')).set_offset(2)


def select2_lookup(**keywords):
    """ requires minlen, tag, placeholder, parenttag """
    if keywords.get('usetag', True):
        keywords['template'] = "templateSelection: function(data, container) { return data.text.split('|', 1); },"
    else:
        keywords['template'] = ''
    if not keywords['tag'].startswith('.'):
        keywords['tag'] = "#" + keywords['tag']
    return '''
  $('%(tag)s').select2( {
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
    return t.div(*args, class_=class_, **kwargs)


def row(*args, **kwargs):
    if CLASS in kwargs:
        class_ = 'row ' + kwargs[CLASS]
        del kwargs[CLASS]
    else:
        class_ = 'row'
    return t.div(*args, class_=class_, **kwargs)


def button(*args, **kwargs):
    if CLASS in kwargs:
        class_ = 'btn btn-info ' + kwargs[CLASS]
        del kwargs[CLASS]
    else:
        class_ = 'btn btn-info'
    return t.span(*args, class_=class_, **kwargs)

# EOF
