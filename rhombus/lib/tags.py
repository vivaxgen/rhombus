
from webhelpers2.html import escape, url_escape, literal

POST = 'post'
GET = 'get'


class htmltag(object):

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '').strip()
        self.class_ = escape(kwargs.get('class_', ''))
        self.id = kwargs.get('id', '').strip()
        if not self.id:
            self.id = self.name
        self.container = None
        self.contents = []
        self.elements = {}
        self.attrs = {}
        for (key, val) in kwargs.items():
            key = key.lower()
            if key in ['name', 'class_', 'id']:
                continue
            self.attrs[key] = val


    def get_container(self):
        if self.container:
            return self.container.get_container()
        return self


    def add(self, *args):
        root = self.get_container()
        for el in args:
            self.contents.append( el )
            if not isinstance(el, htmltag):
                continue
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

        # to accomodate chaining
        return self


    def get(self, identifier):
        return self.elements[identifier]


    def __contains__(self, identifier):
        return identifier in self.elements


    def attributes(self):
        attrs = []
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
        return literal( str(self) )

    def __getitem__(self, arg):
        if type(arg) == tuple:
            self.add( * list(arg) )
        else:
            self.add( arg )
        return self

    def __repr__(self):
        return '<%s name=%s>' % (self.__class__.__name__, self.name)


class form(htmltag):

    def __init__(self, name, action='#', method=GET, **kwargs):
        super().__init__( name = name, **kwargs )
        self.action = action
        self.method = method


    def __str__(self):
        return literal( form_template.format( name=escape(self.name),
                                action = self.action,
                                method = self.method,
                                contents = '\n'.join( escape(c) for c in self.contents ),
                        ) )


class input_text(htmltag):

    def __init__(self, name, label, value='', info=None, size=8, offset=3,
                    extra_control=None, static=False, **kwargs):
        super().__init__( name = name, **kwargs )
        self.label = label
        self.value = value
        self.error = None
        self.info = info
        self.size = size
        self.offset = offset
        self.extra_control = extra_control
        self.static = static

    def __str__(self):
        if self.static:
            return self.as_static()
        return self.as_input()

    def as_input(self):
        if self.info:
            if self.info.startswith('popup:'):
                info = '<div class="col-md-1 form-control-static"><a class="js-newWindow" data-popup="width=400,height=200,scrollbars=yes" href="%s"><span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></a></div>' % self.info[6:]
            else:
                info = ''
        else:
            info = ''
        return literal( input_text_template.format( name=escape(self.name),
                        label=escape(self.label), value=escape(self.value),
                        class_div = 'form-group' + (' has-error' if self.error else ''),
                        class_label = 'col-md-%d control-label' % self.offset,
                        class_value = 'col-md-%d' % self.size,
                        class_input = 'form-control',
                        help_span = self.help(),
                        info = info,
                    ) )

    def help(self):
        if not self.error:
            return ''
        return '<span id="helpBlock" class="help-block">' + self.error + '</span>'

    def add_error(self, errmsg):
        self.error = errmsg

    def as_static(self):
        return literal( input_static_template.format( name=escape(self.name),
                        label=escape(self.label), value=escape(self.value),
                        class_div = 'form-group' + (' has-error' if self.error else ''),
                        class_label = 'col-md-%d control-label' % self.offset,
                        class_value = 'col-md-%d' % self.size,
                        class_input = 'form-control',
                    ) )


class input_show(input_text):

    def __str__(self):
        return self.as_static()


class input_password(input_text):

    def __str__(self):
        if self.info:
            if self.info.startswith('popup:'):
                info = '<div class="col-md-1 form-control-static"><a class="js-newWindow" data-popup="width=400,height=200,scrollbars=yes" href="%s"><span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></a></div>' % self.info[6:]
            else:
                info = ''
        else:
            info = ''
        return literal( input_password_template.format( name=escape(self.name),
                        label=escape(self.label), value=escape(self.value),
                        class_div = 'form-group' + (' has-error' if self.error else ''),
                        class_label = 'col-md-%d control-label' % self.offset,
                        class_value = 'col-md-%d' % self.size,
                        class_input = 'form-control',
                        help_span = self.help(),
                        info = info,
                    ) )

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
                        class_input = 'form-control',
                        extra_control = literal(self.extra_control) if self.extra_control else '',
                        style = 'style="font-family:monospace;"'
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
        self.options = options
        self.multiple = multiple
        self.extra_control = extra_control

    def __str__(self):
        options = []
        for val, label in self.options:
            selected = ''
            if self.value and self.value == val:
                selected = 'selected="selected"'
            options.append( '<option value="%s" %s>%s</option>' %
                        (escape(val), selected, escape(label) ))
        return literal( input_select_template.format(
                    name = escape(self.name), label = escape(self.label),
                    value = escape(self.value),
                    options = '\n'.join(options),
                    multiple = 'multiple="multiple"' if self.multiple else '',
                    class_div = 'form-group',
                    class_label = 'col-md-3 control-label',
                    class_value = 'col-md-%d' % self.size,
                    class_input = 'form-control',
                    extra_control = literal(self.extra_control) if self.extra_control else '',
                ))

    def set(self, options=None, value=None, extra_control=None):
        if options:
            self.options = options
        if value:
            self.value = value
        if extra_control:
            self.extra_control = extra_control


class input_select_ek(input_select):

    def __init__(self, name, label, value, parent_ek, group=None, **kwargs):
        super().__init__( name, label, value, multiple=False, **kwargs )
        self.options = [ (ek.id, ek.key) for ek in parent_ek.members ]


class input_file(input_text):

    def as_input(self):
        if self.info:
            if self.info.startswith('popup:'):
                info = '<div class="col-md-1 form-control-static"><a class="js-newWindow" data-popup="width=400,height=200,scrollbars=yes" href="%s"><span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></a></div>' % self.info[6:]
            else:
                info = ''
        else:
            info = ''
        return literal( input_file_template.format( name=escape(self.name),
                        label=escape(self.label), value=escape(self.value),
                        class_div = 'form-group' + (' has-error' if self.error else ''),
                        class_label = 'col-md-%d control-label' % self.offset,
                        class_value = 'col-md-%d' % self.size,
                        class_input = 'form-control',
                        help_span = self.help(),
                        info = info,
                        extra_control = literal(self.extra_control) if self.extra_control else '',
                    ) )


class checkboxes(htmltag):

    def __init__(self, name, label, boxes, static=False):
        """ boxes: list of [ (name, label, value), ... ] """
        super().__init__( name = name )
        self.label = label
        self.static = static
        for (box_name, box_label, box_value) in boxes:
            self.add( checkbox_item(box_name, box_label, box_value, static ) )

    def __str__(self):
        return literal( checkboxes_template.format(
                class_div = 'form-group',
                class_label = 'col-md-3 control-label',
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
            '<div class="checkbox">'
                '<label><input type="checkbox" name="%s" id="%s" %s />%s</label>'
            '</div>' % ( self.name, self.id, 'checked' if self.value else '', self.label )
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

class input(htmltag):

    _tag = 'input'

    def __str__(self):
        return literal( '<%s %s />' % (self._tag, self.attributes()))

class br(htmltag):

    _tag = 'br'

    def __str__(self):
        return literal( '<%s %s />' % (self._tag, self.attributes()))


class fieldset(doubletag):
    _tag = 'fieldset'

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

class li(doubletag):
    _tag = 'li'


class button(doubletag):
    _tag = 'button'

    def __init__(self, label, **kwargs):
        super().__init__( **kwargs )
        self.label = label

    def __str__(self):
        return literal( '<%s %s>\n%s\n</%s>' % ( self._tag, self.attributes(),
                                self.label, self._tag ) )


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

    def set_offset(self, offset):
        self.offset = offset
        return self

    def __str__(self):
        html = div(class_='form-group')
        buttons = div(class_='col-md-10 col-md-offset-%d' % self.offset)
        for b in self.buttons:
            buttons.add(
                button(class_="btn btn-primary", type="submit", name="_method",
                        id="_method.%s" % b[1], label=b[0], value=b[1])
            )
        buttons.add( button(class_="btn", type="reset", label="Reset") )
        html.add(buttons)
        return literal(html)


## Templates

input_text_template = '''\
<div class='{class_div}'>
  <label class='{class_label}' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <input type='text' id='{name}' name='{name}' value='{value}' class='{class_input}'/>
    {help_span}
  </div>
  {info}
</div>'''

input_password_template = '''\
<div class='{class_div}'>
  <label class='{class_label}' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <input type='password' id='{name}' name='{name}' value='{value}' class='{class_input}'/>
    {help_span}
  </div>
  {info}
</div>'''

input_static_template = '''\
<div class='{class_div}'>
  <label class='{class_label}' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <p class='form-control-static'>{value}</p>
  </div>
</div>'''

input_hidden_template = '''\
<input type='hidden' id='{name}' name='{name}' value='{value}' />
'''

input_textarea_template = '''\
<div class='{class_div}'>
  <label class='{class_label}' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <textarea id='{name}' name='{name}' class='{class_input}' rows='{rows}' {style}>{value}</textarea>
    {extra_control}
  </div>
</div>'''

input_select_template = '''\
<div class='{class_div}'>
  <label class='{class_label}' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <select id='{name}' name='{name}' class='{class_input}' {multiple}>
    {options}
    </select>
    {extra_control}
  </div>
</div>'''

input_file_template = '''\
<div class='{class_div}'>
  <label class='{class_label}' for='{name}'>{label}</label>
  <div class='{class_value}'>
    <input type='file' id='{name}' name='{name}' value='{value}'/>
    {help_span}
    {extra_control}
  </div>
  {info}
</div>'''

checkboxes_template = '''\
<div class='{class_div}'>
  <label class='{class_label}'>{label}</label>
  <div class='{class_value}'>
    {boxes}
  </div>
</div>'''

radioboxes_template = '''\
<div class='{class_div}'>
  <label class='{class_label'}>{label}</label>
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
<div class='form-group'>
  <div class='col-md-10 col-md-offset-3'>
    <button class='btn btn-primary' type='submit' name='_method' value='{val}'>{label}</button>
    <button class='btn' type='reset'>Reset</button>
  </div>
</div>
'''

form_template = '''\
<form name="{name}" id="{name}" action="{action}" method="{method}" class="form-horizontal input-group-sm">
  {contents}
</form>'''

