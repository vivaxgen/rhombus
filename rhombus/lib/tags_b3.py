
from webhelpers2.html import escape, url_escape, literal

POST = 'post'
GET = 'get'


class htmltag(object):

    def __init__(self, **kwargs):
        self.set_name(kwargs.get('name', '').strip())
        self.class_ = escape(kwargs.get('class_', ''))
        self.set_id(kwargs.get('id', '').strip())
        #if not self.id:
        #    self.id = self.name
        self.container = None
        self.contents = []
        self.elements = {}
        self.attrs = {}
        for (key, val) in kwargs.items():
            key = key.lower()
            if key in ['name', 'class_', 'id']:
                continue
            self.attrs[key.removesuffix('_')] = val
        self.enabled = True

    def set_name(self, name):
        self.name = name

    def set_id(self, an_id):
        self.id = an_id
        if not self.id:
            self.id = self.name

    def get_container(self):
        if self.container:
            return self.container.get_container()
        return self

    def register_element(self, el):
        root = self.get_container()
        if not isinstance(el, htmltag):
            return
        if el.id:
            identifier = el.id
            if identifier in root.elements:
                raise RuntimeError('duplicate element id/name: %s' % identifier)
            root.elements[identifier] = el
        for (identifier, value) in el.elements.items():
            if identifier in root.elements:
                raise RuntimeError('duplicate element id/name: %s' % identifier)
            root.elements[identifier] = value
        el.container = self

    def add(self, *args):
        for element in args:
            self.contents.append(element)
            self.register_element(element)

        # to accomodate chaining
        return self

    def insert(self, index, *elements):
        for element in reversed(elements):
            self.contents.insert(index, element)
            self.register_element( element )
        return self

    def get(self, identifier):
        return self.elements[identifier]

    def __contains__(self, identifier):
        return identifier in self.elements

    def __iadd__(self, element):
        return self.add(element)

    def attributes(self, attrs_only=False):
        attrs = []
        if not attrs_only:

            if self.name or self.id:
                attrs.append('name="%s" id="%s"' % (escape(self.name or self.id),
                             escape(self.id or self.name)))
            if self.class_:
                attrs.append('class="%s"' % escape(self.class_))

        for (key, val) in self.attrs.items():
            attrs.append('%s="%s"' % (escape(key), escape(val)))
        return ' '.join(attrs)

    def __call__(self):
        return str(self)

    def __html__(self):
        if not self.enabled:
            return ''
        return literal(str(self))

    def __getitem__(self, arg):
        if type(arg) == tuple:
            self.add(* list(arg))
        else:
            self.add(arg)
        return self

    def __repr__(self):
        return '<%s name=%s>' % (self.__class__.__name__, self.name)

    def div_wrap(self, html):
        if isinstance(self.container, multi_inputs):
            return html
        return str(div(html, class_='form-group form-inline row'))

    def enable(self, flag=True):
        self.enabled = flag


FORM_URLENCODED = 'application/x-www-form-urlencoded'
FORM_MULTIPART = 'multipart/form-data'


class form(htmltag):

    def __init__(self, name, action='#', method=GET, enctype=FORM_URLENCODED, **kwargs):
        super().__init__(name=name, **kwargs )
        self.action = action
        self.method = method
        self.enctype = enctype


    def __str__(self):
        return literal( form_template.format( name=escape(self.name),
                                action = self.action,
                                method = self.method,
                                enctype = self.enctype,
                                contents = '\n'.join( escape(c) for c in self.contents ),
                        ) )


class input_text(htmltag):

    def __init__(self, name, label, value='', info=None, size=8, offset=3,
                 extra_control=None, static=False, placeholder='', update_dict=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.label = label
        self.value = (update_dict.get(name, None) if update_dict else value) or value
        self.placeholder = placeholder
        self.error = None
        self.info = info
        self.size = size
        self.offset = offset
        self.extra_control = extra_control
        self.static = static

    def __str__(self):
        return self.as_input()

    def as_input(self, value=None, static=False):
        return literal(
            input_text_template.format(
                name=escape(self.name),
                label=escape(self.label), value=escape(value or self.value),
                placeholder=self.placeholder,
                class_div='form-group',
                class_label='col-md-%d control-label d-flex justify-content-end' % self.offset,
                class_value='col-md-%d' % self.size,
                class_input='form-control' + (' is-invalid' if self.error else ''),
                help_span=self.help(),
                info=self.info_text(),
                ro='readonly' if (self.static or static) else '',
            )
        )

    def help(self):
        if not self.error:
            return ''
        return '<span id="invalid-feedback" class="invalid-feedback">' + self.error + '</span>'

    def add_error(self, errmsg):
        self.error = errmsg

    def as_static(self, value=None):
        return self.as_input(value=value, static=True)

    def info_text(self):
        if self.info:
            if self.info.startswith('popup:'):
                info = '<div class="col-md-1 form-control-static"><a class="js-newWindow" data-popup="width=400,height=200,scrollbars=yes" href="%s"><span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></a></div>' % self.info[6:]
            else:
                info = '<small class="form-text text-muted">' + self.info + '</small>'
        else:
            info = ''
        return info

    def ro(self):
        return 'readonly' if self.static else ''


class input_show(input_text):

    def __str__(self):
        return self.as_static()


class input_password(input_text):

    def __str__(self):
        return literal(
            input_password_template.format(
                name=escape(self.name),
                label=escape(self.label), value=escape(self.value),
                class_div='form-group',
                class_label='col-md-%d control-label d-flex justify-content-end' % self.offset,
                class_value='col-md-%d' % self.size,
                class_input='form-control' + (' is-invalid' if self.error else ''),
                help_span=self.help(),
                info=self.info_text(),
            )
        )

class input_textarea(input_text):

    def __str__(self):
        if type(self.size) == str and 'x' in self.size:
            rows,size = ( int(v) for v in self.size.split('x') )
        else:
            rows,size = 4, self.size
        return literal( input_textarea_template.format( name=escape(self.name),
                        label=escape(self.label), value=escape(self.value),
                        class_div = 'form-group',
                        class_label = 'col-md-%d control-label' % self.offset,
                        class_value = 'col-md-%d' % size,
                        rows = rows,
                        class_input = 'form-control'  + (' is-invalid' if self.error else ''),
                        extra_control = literal(self.extra_control) if self.extra_control else '',
                        style = 'style="font-family:monospace; width:100%;"',
                        help_span = self.help(),
                        info = self.info_text(),
                        ro = 'readonly' if self.static else '',
                    ) )

class input_hidden(htmltag):

    def __init__(self, name, value, **kwargs):
        super().__init__( name = name, **kwargs )
        self.name = name
        self.value = value

    def __str__(self):
        return literal( '<input type="hidden" id="%s" name="%s" value="%s" />' %
                        (escape(self.id or self.name), escape(self.name), escape(self.value)) )


class input_select(input_text):

    def __init__(self, name, label, value='', options=[], multiple=False, extra_control=None, **kwargs):
        """ options: [ (val, label), ... ] """
        super().__init__( name, label, value, **kwargs )
        self.options = [ (str(o[0]), o[1]) for o in options ]
        self.multiple = multiple
        self.extra_control = extra_control
        if self.multiple:
            self.value = [ str(x) for x in self.value ]
        else:
            self.value = str(self.value)

    def __str__(self):
        if self.static:
            if self.multiple:
                value = ' '.join([l for (v,l) in self.options if v in self.value]) or ' '
            else:
                value = ' '
                for (v,l) in self.options:
                    if v == self.value:
                        value = l
                        break
            return self.as_static(value)

        options = []
        for val, label in self.options:
            selected = ''
            if self.value:
                if self.multiple:
                    if type(self.value) != list:
                        raise RuntimeError('input_select() with multiple options needs a list as value')
                    if val in self.value:
                        selected = 'selected="selected"'
                elif val == self.value:
                    selected = 'selected="selected"'
            options.append('<option value="%s" %s>%s</option>' %
                           (escape(val), selected, escape(label)))
        html = literal(
            input_select_template.format(
                name=escape(self.name), label=escape(self.label),
                value=escape(self.value),
                options='\n'.join(options),
                multiple='multiple="multiple"' if self.multiple else '',
                class_label='col-md-%d control-label d-flex justify-content-end' % self.offset,
                class_value='col-md-%d' % self.size,
                class_input='form-select' + (' is-invalid' if self.error else ''),
                attrs=self.attributes(attrs_only=True),
                help_span=self.help(),
                info=self.info_text(),
                extra_control=literal(self.extra_control) if self.extra_control else '',
            )
        )
        return self.div_wrap(html)

    def set(self, options=None, value=None, extra_control=None):
        if options:
            self.options = options
        if value:
            self.value = value
        if extra_control:
            self.extra_control = extra_control


class input_select_ek(input_select):

    def __init__(self, name, label, value, parent_ek, group=None, option_filter=None, **kwargs):
        if parent_ek is None:
            raise RuntimeError('parent_ek cannot be None')
        super().__init__(name, label, value, multiple=False, **kwargs)
        self.options = [(str(ek.id), ek.key) for ek in parent_ek.members]
        if option_filter:
            self.options = [opt for opt in self.options if option_filter(opt[1])]


class input_file(input_text):

    def as_input(self):
        return literal( input_file_template.format( name=escape(self.name),
                        label=escape(self.label), value=escape(self.value),
                        class_div = 'form-group' + (' has-error' if self.error else ''),
                        class_label = 'col-md-%d control-label' % self.offset,
                        class_value = 'col-md-%d' % self.size,
                        class_input = 'form-control-file',
                        help_span = self.help(),
                        info = self.info_text(),
                        view_link=self.view_link(),
                        extra_control = literal(self.extra_control) if self.extra_control else '',
                    ) )

    def __str__(self):
        if self.static:
            # show as static; label and view link (open new tab)
            return literal(input_plaintext_template.format(
                        name=escape(self.name),
                        label=escape(self.label), value=escape(self.value),
                        placeholder=self.placeholder,
                        class_div = 'form-group',
                        class_label = 'col-md-%d control-label' % self.offset,
                        class_value = 'col-md-%d' % self.size,
                        class_input = 'form-control' + (' is-invalid' if self.error else ''),
                        text=self.value,
                        help_span = self.help(),
                        info = self.info_text(),
                )
            )
        else:
            return self.as_input()

    def set_view_link(self, html):
        self._view_link = html
        return self

    def view_link(self):
        if hasattr(self, '_view_link'):
            return self._view_link
        return ''


class input_file_attachment(input_file):

    def set_view_link(self, html):
        self._view_link = html
        return self

    def set_routefunc(self, routefunc):
        self._routename = routefunc

    def view_link(self):
        if self.value is None:
            return 'Not available'
        if hasattr(self, '_view_link'):
            return literal(self._view_link)
        return ''

    def __str__(self):
        if self.static:
            # show as static; label and view link (open new tab)
            return literal(input_plaintext_template.format(
                        name=escape(self.name),
                        label=escape(self.label), value=escape(self.value),
                        placeholder=self.placeholder,
                        class_div = 'form-group',
                        class_label = 'col-md-%d control-label' % self.offset,
                        class_value = 'col-md-%d' % self.size,
                        class_input = 'form-control' + (' is-invalid' if self.error else ''),
                        text=self.view_link(),
                        help_span = self.help(),
                        info = self.info_text(),
                )
            )
        else:
            return self.as_input()


class checkboxes(htmltag):

    def __init__(self, name, label, boxes, offset=3, static=False, **kwargs):
        """ boxes: list of [ (name, label, value), ... ] """
        super().__init__( name = name, **kwargs )
        self.label = label
        self.offset = offset
        self.static = static
        for (box_name, box_label, box_value) in boxes:
            self.add( checkbox_item(box_name, box_label, box_value, static ) )

    def __str__(self):
        return literal( checkboxes_template.format(
                class_div = 'form-group',
                class_label = 'col-md-%d control-label' % self.offset,
                class_value = 'col-md-8',
                label = self.label,
                boxes = '\n'.join( str(item) for item in self.contents )
            ))


class checkbox_item(htmltag):

    def __init__(self, name, label, value, static=False):
        super().__init__( name = name )
        self.label = label
        self.value = value
        self.static = static

    def __str__(self):
        return literal(
            '<div class="form-check form-check-inline justify-content-start">'
                '<input type="checkbox" class="form-check-input" name="%s" id="%s" %s />'
                '<label class="form-check-label" for="%s">%s</label>'
            '</div>' % ( self.name, self.id, 'checked' if self.value else '', self.id, self.label )
            )


class radioboxes(htmltag):

    def __init__(self, name, label, value, boxes, static=False):
        """ boxes: list of [ (label, value), ...] """
        super().__init__( name = name )
        self.label = label
        self.boxes = boxes
        self.static = static

    def __str__(self):
        boxes = []
        for (idx, box) in enumerate(self.boxes):
            boxes.append(
                literal(
                    '<div class="radio">'
                        '<label>'
                            '<input type="radio" name="%s" id="%s" %s />'
                            '%s'
                        '</label>'
                    '</div>' % (self.name, self.id + '%02d' % idx,
                                    'checked' if self.value == box[1] else '',
                                    box[0])
                )
            )
        return literal( checkboxes_template.format(
                class_div = 'form-group',
                class_label = 'col-md-3 control-label',
                class_value = 'col-md-8',
                label = self.label,
                boxes = '\n'.join( boxes )
            ))


class doubletag(htmltag):

    _tag = ''

    def __init__(self, *args, **kwargs):
        super().__init__( **kwargs )
        self.add( *args )

    def __str__(self):
        return literal( '<%s %s>%s</%s>' % ( self._tag, self.attributes(),
                                    '\n'.join( escape(c) for c in self.contents ),
                                    self._tag )
                )

class image(htmltag):

    _tag = 'image'

    def __str__(self):
        return literal( '<%s %s />' % (self._tag, self.attributes()))

class inputtag(htmltag):

    _tag = 'input'

    def __str__(self):
        return literal( '<%s %s />' % (self._tag, self.attributes()))

input = inputtag


class br(htmltag):

    _tag = 'br'

    def __str__(self):
        return literal('<%s %s />' % (self._tag, self.attributes()))


class hr(br):

    _tag = 'hr'


class fieldset(doubletag):
    _tag = 'fieldset'

class label(doubletag):
    _tag = 'label'

class p(doubletag):
    _tag = 'p'

class h1(doubletag):
    _tag = 'h1'

class h2(doubletag):
    _tag = 'h2'

class h3(doubletag):
    _tag = 'h3'

class h4(doubletag):
    _tag = 'h4'

class h5(doubletag):
    _tag = 'h5'

class span(doubletag):
    _tag = 'span'

class a(doubletag):
    _tag = 'a'

class b(doubletag):
    _tag = 'b'

class i(doubletag):
    _tag = 'i'

class div(doubletag):
    _tag = 'div'

    def __str__(self):
        return literal( '<%s %s>\n%s\n</%s>' % ( self._tag, self.attributes(),
                                        '\n'.join( escape(c) for c in self.contents ),
                                        self._tag ) )

class pre(doubletag):
    _tag = 'pre'

class ul(doubletag):
    _tag = 'ul'

    def __init__(self, *args, **kwargs):
        super().__init__( **kwargs )
        self.add_contents( *args )

    def add_contents(self, *args):
        for arg in args:
            if not isinstance(args, li):
                raise RuntimeError('UL should only have LI content')
            self.contents.append(arg)

class ol(ul):
    _tag = 'ol'

class li(doubletag):
    _tag = 'li'

class dl(doubletag):
    _tag = 'dl'

class dt(doubletag):
    _tag = 'dt'

class dd(doubletag):
    _tag = 'dd'


class button(doubletag):
    _tag = 'button'

    def __init__(self, label, **kwargs):
        super().__init__( **kwargs )
        self.label = label

    def __str__(self):
        return literal( '<%s %s>\n%s\n</%s>' % ( self._tag, self.attributes(),
                                self.label, self._tag ) )


class nav(doubletag):
    _tag = 'nav'


## tables

class table(doubletag):
    _tag = 'table'

class thead(doubletag):
    _tag = 'thead'

class tbody(doubletag):
    _tag = 'tbody'

class tr(doubletag):
    _tag = 'tr'

class th(doubletag):
    _tag = 'th'

class td(doubletag):
    _tag = 'td'

## singleton

BR = literal('<br/>')
HR = literal('<hr/>')

## composites

class submit_bar(htmltag):

    def __init__(self, label='Save', value='save'):
        super().__init__()
        self.label = label
        self.value = value

    def __str__(self):
        return literal( submit_bar_template.format( label = self.label, val = self.value ) )

class custom_submit_bar(htmltag):

    def __init__(self, *args):
        # args: ('Save', 'save'), ('Continue', 'continue')
        super().__init__()
        self.buttons = args
        self.offset=3
        self.hide = False
        self.reset_button = True

    def set_offset(self, offset):
        self.offset = offset
        return self

    def set_hide(self, flag):
        self.hide = flag
        return self

    def show_reset_button(self, flag):
        self.reset_button = flag
        return self

    def __str__(self):
        html = div(class_='form-group', style='display: none' if self.hide else '')
        buttons = div(class_='col-md-10 offset-md-%d' % self.offset)
        for b in self.buttons:
            buttons.add(
                button(class_="btn btn-primary", type="submit", name="_method",
                        id="_method.%s" % b[1], label=b[0], value=b[1])
            )
        if self.reset_button:
            buttons.add( button(class_="btn", type="reset", label="Reset") )
        html.add(buttons)
        return literal(html)


class selection_bar(object):

    def __init__(self, prefix, action, add=None, others='', hiddens=[], name='', delete_value='delete'):
        super().__init__()
        self.prefix = prefix
        self.action = action
        self.add = add
        self.others = others
        self.hiddens = hiddens
        self.name = name or 'selection_bar'
        self.delete_value = delete_value

    def render(self, html, jscode=''):

        button_bar = div(class_='btn-toolbar')[
            div(class_='btn-group')[
                button(label="Select all", type='button', class_='btn btn-sm btn-secondary', id=self.prefix + '-select-all'),
                button(label="Unselect all", type='button', class_="btn btn-sm btn-secondary", id=self.prefix + '-select-none'),
                button(label='Inverse', type='button', class_='btn btn-sm btn-secondary', id=self.prefix + '-select-inverse')
            ],
            div(class_='btn-group')[
                button(label="<i class='icon-trash icon-white'></i> Delete",
                        class_="btn btn-sm btn-danger", id=self.prefix + '-submit-delete',
                        name='_method', value=self.delete_value, type='button')
            ]
        ]

        if self.add:
            button_bar.add(
                div(class_='btn-group')[
                    a(href=self.add[1])[
                        button(label=self.add[0], type='button', class_='btn btn-sm btn-success')
                    ]
                ]
            )

        if self.others:
            button_bar.add(
                div(class_='btn-group')[ self.others ]
            )

        if self.hiddens:
            hiddens = div()
            for (k, v) in self.hiddens:
                hiddens.add(
                    literal('<input type="hidden" name="%s" value="%s" />'
                    % (k, v))
                    )
        else:
            hiddens = ''

        sform = form(name=self.name, method='post', action=self.action)
        sform.add(
            div(id=self.prefix + '-modal', class_='modal fade', role='dialog', tabindex='-1'),
            button_bar,
            html,
            hiddens
        )

        return sform, jscode + selection_bar_js % { 'prefix': self.prefix }


class multi_inputs(div):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, class_='form-group form-inline row', **kwargs)


## Templates

input_text_template = '''\
<div class='{class_div} form-inline row'>
  <label class='{class_label} align-self-start pt-2' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <input type='text' id='{name}' name='{name}' value='{value}' class='{class_input}' placeholder='{placeholder}' style='width:100%' {ro}/>
    {help_span}
  </div>
  {info}
</div>'''

input_plaintext_template = '''\
<div class='{class_div} form-inline row'>
  <label class='{class_label} ' for='{name}'>{label}</label>
  <div class='{class_value}'>
    {text}
    {help_span}
  </div>
  {info}
</div>'''

input_password_template = '''\
<div class='{class_div} form-inline row'>
  <label class='{class_label} align-self-start pt-2' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <input type='password' id='{name}' name='{name}' value='{value}' class='{class_input}' style='width:100%'/>
    {help_span}
  </div>
  {info}
</div>'''

input_static_template = '''\
<div class='{class_div} form-inline row'>
  <label class='{class_label}' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <input type='text' class='{class_input}' value='{value}' readonly />
  </div>
</div>'''

input_hidden_template = '''\
<input type='hidden' id='{name}' name='{name}' value='{value}' />
'''

input_textarea_template = '''\
<div class='{class_div} form-inline row'>
  <label class='{class_label} align-self-baseline pt-2' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <textarea id='{name}' name='{name}' class='{class_input}' rows='{rows}' {style} {ro}>{value}</textarea>
    {extra_control}
    {help_span}
    {info}
  </div>
</div>'''

input_select_template = '''\
  <label class='{class_label} align-self-start pt-2' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <select id='{name}' name='{name}' class='{class_input}' {multiple} {attrs} style='width:100%'>
    {options}
    </select>
    {extra_control}
    {help_span}
    {info}
  </div>
'''

input_file_template = '''\
<div class='{class_div} form-inline row'>
  <label class='{class_label} align-self-start pt-1' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <input type='file' id='{name}' class='{class_input}' name='{name}' value='{value}'/>
    {help_span}
    {extra_control}
    {info}
  </div>
  {view_link}
</div>'''

checkboxes_template = '''\
<div class='{class_div} form-inline row'>
  <label class='{class_label} align-self-baseline pt-2'>{label}</label>
  <div class='{class_value}'>
    {boxes}
  </div>
</div>'''

radioboxes_template = '''\
<div class='{class_div}'>
  <label class='{class_label} justify-content-baseline pt-2'>{label}</label>
  <div class='{class_value}'>
    {boxes}
  </div>
</div>'''

radioboxes_template_xxx = '''\
<div class="{class_div}">
  <label class="{class_label}" for="{name}">{label}</label>
  % for (n, l, c) in params:
  <div class="controls">
    <label class="checkbox">
      <input id="${name}" type="checkbox" name="${n}" value="1" ${"checked='checked'" if c else ''} />
      ${l}
    </label>
  </div>
  % endfor
</div>'''

submit_bar_template = '''\
<div class='form-group row'>
  <div class='col-md-10 offset-md-3'>
    <button class='btn btn-primary' type='submit' name='_method' value='{val}'>{label}</button>
    <button class='btn' type='reset'>Reset</button>
  </div>
</div>
'''

form_template = '''\
<form name="{name}" id="{name}" action="{action}" method="{method}" class="form-horizontal input-group-sm" enctype="{enctype}">
  {contents}
</form>'''

selection_bar_js = '''\
  $('#%(prefix)s-select-all').click( function() {
        $('input[name="%(prefix)s"]').each( function() {
            this.checked = true;
        });
    });

  $('#%(prefix)s-select-none').click( function() {
        $('input[name="%(prefix)s"]').each( function() {
            this.checked = false;
        });
    });

  $('#%(prefix)s-select-inverse').click( function() {
        $('input[name="%(prefix)s"]').each( function() {
            if (this.checked == true) {
                this.checked = false;
            } else {
                this.checked = true;
            }
        });
    });

  $('#%(prefix)s-submit-delete').click( function(e) {
        var form = $(this.form);
        var data = form.serializeArray();
        data.push({ name: $(this).attr('name'), value: $(this).val() });
        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: data,
            success: function(data, status) {
                $('#%(prefix)s-modal').html(data);
                $('#%(prefix)s-modal').modal('show');
            }
        });
    });
'''
