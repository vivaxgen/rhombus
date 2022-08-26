#
#  this module defines input tags for bootstrap 5.2
#

from webhelpers2.html import escape, url_escape, literal
from .coretags import (FORM_URLENCODED, FORM_MULTIPART, GET, POST, htmltag, doubletag, div, span, label,
                       inputtag, selecttag, textareatag, optiontag, button, a, i)


class inline_inputs(div):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, class_='form-group form-inline row', **kwargs)

    def get_container_xxx(self):
        return self.container.get_container()


class form(doubletag):
    """ form is a container as well """
    _t = 'form'

    def __init__(self, name, action='#', method=POST, readonly=False, update_dict=None, enctype=FORM_URLENCODED, **kwargs):
        super().__init__(name=name, **(kwargs | dict(method=method, action=action, enctype=enctype)))
        self.readonly = readonly
        self.update_dict = update_dict

    def set_readonly(self, readonly=True):
        self.readonly = readonly

    def ro(self):
        return self.readonly

    def get_container(self):
        """ root container is form """
        return self


class input_text(htmltag):
    _type = 'text'

    def __init__(self, name, label, value='', info=None, size=8, offset=3, style=None,
                 extra_control=None, readonly=False, placeholder='', update_dict=None,
                 popover=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.label = label
        #self.value = (update_dict.get(name, None) if update_dict else value) or value
        self.value = value
        self.update_dict = update_dict
        self.placeholder = placeholder
        self.error = None
        self.info = info
        self.size = size
        self.offset = offset
        self._extra_control = extra_control or ''
        self.readonly = readonly
        self._style = style
        self.popover = popover

    def error_text(self):
        if not self.error:
            return ''
        return span(id="invalid-feedback", class_="invalid-feedback")[self.error]

    def add_error(self, errmsg):
        self.error = errmsg

    def style(self):
        return self._style or 'width:100%'

    def set_style(self, style):
        self._style = style
        return self

    def extra_control(self):
        return self._extra_control

    def set_extra_control(self, extra_control):
        self._extra_control = extra_control
        return self

    def info_text(self):
        if self.info:
            if self.info.startswith('popup:'):
                info = literal('<div class="col-md-1 form-control-static">'
                               '<a class="js-newWindow" data-popup="width=400,height=200,scrollbars=yes" href="%s">'
                               '<span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span>'
                               '</a></div>' % self.info[6:])
            else:
                info = literal('<small class="form-text text-muted">' + self.info + '</small>')
        else:
            info = ''
        return info

    def get_form(self):
        # travesing through containers to get form
        c = self
        while (c := c.container):
            if isinstance(c, form):
                return c
        return None

    def get_value(self):
        if self.update_dict is False:
            return self.value
        if self.update_dict is None:
            # check form
            form = self.get_form()
            if form.update_dict in [False, None]:
                return self.value
            return form.update_dict.get(self.name, None) or self.value
        return self.update_dict.get(self.name, None) or self.value

    def ro(self):
        return self.readonly or self.get_form().readonly

    def class_value(self, size=None):
        return f'col-md-{self.size or size} pl-2'

    def class_label(self):
        return f'col-md-{self.offset} control-label'

    def class_input(self):
        return 'form-control pl-2 pr-2' + (' is-invalid' if self.error else '')

    def class_div(self):
        return 'form-group'

    def div_wrap(self, elements):
        if not isinstance(self.container, inline_inputs):
            return div(class_='form-group form-inline row').add(*elements).r()
        return self.r_contents(elements)

    def as_plaintext(self, value=None):
        elements = [
            label(self.label, class_=f"{self.class_label()} align-self-start pt-2 pb-2 pl-1 pr-0", for_=self.name),
            div(class_=self.class_value() + 'pl-10')[
                value or self.value,
                self.error_text()
            ],
            self.info_text()
        ]
        return self.div_wrap(elements)

    def r(self, value=None, readonly=False):
        # set value first
        pop_title, pop_content = self.popover.split('|', 2) if self.popover else ('', '')
        elements = [
            label(self.label,
                  class_=f"{self.class_label()} d-flex justify-content-end align-self-start pt-2 pl-1 pr-0",
                  for_=self.name,
                  **{'data-toggle': 'popover', 'data-placement': 'top',
                     'title': pop_title, 'data-content': pop_content})
            if self.label is not None else '',
            div(class_=self.class_value())[
                inputtag(type=self._type, id=self.id, name=self.name,
                         value=value or self.get_value(), class_=self.class_input(), placeholder=self.placeholder,
                         style=self.style(), readonly=self.ro() or readonly),
                self.error_text()
            ],
            self.info_text()
        ]
        return self.div_wrap(elements)


class input_hidden(htmltag):

    def __init__(self, name, value, **kwargs):
        super().__init__(name=name, **kwargs)
        self.value = value

    def r(self):
        return inputtag(type='hidden', id=self.id or self.name, name=self.name or self.id, value=self.value).r()


class input_password(input_text):
    _type = 'password'


class input_textarea(input_text):

    def style(self):
        return self._style or "font-family:monospace; font-size:0.9em; width:100%;"

    def r(self):
        # set size first
        if type(self.size) == str and 'x' in self.size:
            rows, size = (int(v) for v in self.size.split('x'))
        else:
            rows, size = 4, self.size

        return div(class_='form-group form-inline row')[
            label(self.label,
                  class_=f"{self.class_label()} d-flex justify-content-end align-self-start pt-2 pl-1 pr-0",
                  for_=self.name),
            div(class_=self.class_value(size))[
                textareatag(id=self.id, name=self.name, class_=self.class_input(), style=self.style(),
                            readonly=self.ro())[self.get_value()],
                self.extra_control(),
                self.error_text()
            ],
            self.info_text()
        ].r()


class input_select(input_text):

    def __init__(self, name, label, value='', options=[], multiple=False, extra_control=None, **kwargs):
        """ options: [ (val, label), ...] """
        super().__init__(name, label, value, extra_control=extra_control, **kwargs)
        self._options = [(str(o[0]), o[1]) for o in options]
        self.multiple = multiple

        # convert ids of values to string for comparison purposes
        if multiple:
            self.value = [str(x) for x in self.value]
        else:
            self.value = str(self.value)

    def options(self):
        return self._options

    def set(self, options=None, value=None, extra_control=None):
        if options:
            self._options = options
        if value:
            self.value = value
        if extra_control:
            self.extra_control = extra_control
        return self

    def class_input(self):
        return 'form-select pl-2 pr-2' + (' is-invalid' if self.error else '')

    def r(self):

        multiple = self.multiple
        if self.ro():
            if multiple:
                value = ' | '.join([l for (v, l) in self.options() if v in self.value]) or ''
            else:
                value = [l for (v, l) in self.options() if v == self.value][0]
            return super().r(value=value)

        # preparing option list
        options = []
        for (v, l) in self.options():
            selected = False
            if self.value:
                if multiple:
                    if type(self.value) != list:
                        raise RuntimeError('input_select() with multiple options needs a list as value')
                    if v in self.value:
                        selected = 'selected'
                elif v == self.value:
                    selected = 'selected'
            options.append(optiontag(l, value=v, selected=selected))

        pop_title, pop_content = self.popover.split('|', 2) if self.popover else ('', '')
        elements = [
            label(self.label,
                  class_=f"{self.class_label()} d-flex justify-content-end align-self-start pt-2 pl-1 pr-0",
                  for_=self.name,
                  **{'data-toggle': 'popover', 'data-placement': 'top',
                     'title': pop_title, 'data-content': pop_content})
            if self.label is not None else '',
            div(class_=self.class_value())[
                selecttag(*options, id=self.id, name=self.name, class_=self.class_input(), multiple=multiple,
                          style=self.style(), readonly=self.ro()),
                self.extra_control(),
                self.error_text()
            ],
            self.info_text()
        ]
        return self.div_wrap(elements)


class input_select_ek(input_select):

    def __init__(self, name, label, value, parent_ek, group=None, option_filter=None, description=False,
                 **kwargs):
        if parent_ek is None:
            raise RuntimeError('parent_ek cannot be None')
        super().__init__(name, label, value, multiple=False, **kwargs)
        if description:
            self._options = [(str(ek.id), f'{ek.key} | {ek.desc}')
                             for ek in parent_ek.members]
        else:
            self._options = [(str(ek.id), ek.key) for ek in parent_ek.members]
        if option_filter:
            self._options = [opt for opt in self._options if option_filter(opt[1])]


class input_file(input_text):
    _type = 'file'

    def set_view_link(self, html):
        self._view_link = html
        return self

    def view_link(self):
        if hasattr(self, '_view_link'):
            return self._view_link
        return ''

    def r(self, value=None):
        if self.ro():
            return self.as_plaintext(value=self.view_link())

        elements = [
            label(self.label,
                  class_=f"{self.class_label()} d-flex justify-content-end align-self-start pt-2 pl-1 pr-0",
                  for_=self.name),
            div(class_=self.class_value())[
                inputtag(type=self._type, id=self.id, name=self.name, class_=self.class_input() + ' pt-1'),
                self.error_text(),
                self.info_text(),
            ],
            self.view_link()
        ]
        return self.div_wrap(elements)


class input_file_attachment(input_file):

    def view_link(self):
        if self.value is None:
            return 'Not available'
        if hasattr(self, '_view_link'):
            return literal(self._view_link)
        return ''


class checkboxes(input_text):

    def __init__(self, name, label, boxes, **kwargs):
        """ boxes: list of [ (name, label, value), ... ] """
        super().__init__(name=name, label=label, **kwargs)
        for (box_name, box_label, box_value) in boxes:
            self.add(checkbox_item(box_name, box_label, box_value))

    def __str__XXX(self):
        return literal( checkboxes_template.format(
                class_div = 'form-group',
                class_label = 'col-md-%d control-label' % self.offset,
                class_value = 'col-md-8',
                label = self.label,
                boxes = '\n'.join( str(item) for item in self.contents )
            ))

    def r(self):
        pop_title, pop_content = self.popover.split('|', 2) if self.popover else ('', '')
        elements = [
            label(self.label,
                  class_=f"{self.class_label()} d-flex justify-content-end align-self-start pt-2 pl-1 pr-0",
                  for_=self.name,
                  **{'data-toggle': 'popover', 'data-placement': 'top',
                     'title': pop_title, 'data-content': pop_content})
            if self.label is not None else '',
            div(*self.contents, class_=self.class_value(), autoregister=False),
            self.info_text()
        ]

        return self.div_wrap(elements)


checkboxes_template = '''\
<div class='{class_div} form-inline row'>
  <label class='{class_label} align-self-baseline pt-2'>{label}</label>
  <div class='{class_value}'>
    {boxes}
  </div>
</div>'''


class checkbox_item(input_text):

    def __init__(self, name, label, value, readonly=False):
        super().__init__(name=name, label=label, value=value, readonly=readonly)


    def __str__XXX(self):
        return literal(
            '<div class="form-check form-check-inline justify-content-start align-self-end pt-2 pl-1 pr-0">'
                '<input type="checkbox" class="form-check-input" name="%s" id="%s" %s />'
                '<label class="form-check-label align-self-end pt-2 pl-1 pr-0" for="%s">%s</label>'
            '</div>' % ( self.name, self.id, 'checked' if self.value else '', self.id, self.label )
            )

    def r(self):
        if self.ro():
            return literal(
                '<div class="form-check form-check-inline justify-content-start align-self-end pt-2 pl-1 pr-0">'
                f'<label class="form-check-label {"badge rounded-pill text-bg-info" if self.value else "text-muted"}">{self.label}</label>'
                '</div>'
            )
        elements = [
            literal('<input type="checkbox" class="form-check-input" name="%s" id="%s" %s />')
        ]
        # raise
        return literal(
            '<div class="form-check form-check-inline justify-content-start align-self-end pt-2 pl-1 pr-0">'
                '<input type="checkbox" class="form-check-input" name="%s" id="%s" %s />'
                '<label class="form-check-label" for="%s">%s</label>'
            '</div>' % ( self.name, self.id, 'checked' if self.value else '', self.id, self.label )
        )

#
# composites

class submit_bar(htmltag):

    def __init__(self, label='Save', value='save'):
        super().__init__()
        self.label = label
        self.value = value

    def __str__(self):
        return literal(submit_bar_template.format(label=self.label, val=self.value))

    def r(self):
        html = div(class_='form-group row')[
            div(class_='col-md-10 offset-md-3')[
                button(self.label, name='_method', class_='btn btn-primary', type='submit',
                       value=self.value),
                button('Reset', type='reset', class_='btn'),
            ]
        ]
        return html.r()


class custom_submit_bar(htmltag):

    def __init__(self, *args):
        # args: ('Save', 'save'), ('Continue', 'continue')
        super().__init__()
        self.buttons = args
        self.offset = 3
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

    def r(self):
        html = div(class_='form-group', style='display: none' if self.hide else '')
        buttons = div(class_='col-md-10 offset-md-%d' % self.offset)
        for b in self.buttons:
            assert type(b) == tuple or type(b) == list
            buttons.add(
                button(b[0], class_="btn btn-primary", type="submit", name="_method",
                       id="_method.%s" % b[1], value=b[1])
            )
        if self.reset_button:
            buttons.add(button(class_="btn", type="reset", label="Reset"))
        html.add(buttons)
        return html.r()


class selection_bar(object):

    def __init__(self, prefix, action, add=None, others='', hiddens=[], name='',
                 delete_label='Delete', delete_value='delete'):
        super().__init__()
        self.prefix = prefix
        self.action = action
        self.add = add
        self.others = others
        self.hiddens = hiddens
        self.name = name or 'selection_bar'
        self.delete_label = delete_label
        self.delete_value = delete_value

    def render(self, html, jscode=''):

        button_bar = div(class_='btn-toolbar')[
            div(class_='btn-group')[
                button("Select all", type='button', class_='btn btn-sm btn-secondary', id=self.prefix + '-select-all'),
                button("Unselect all", type='button', class_="btn btn-sm btn-secondary", id=self.prefix + '-select-none'),
                button('Inverse', type='button', class_='btn btn-sm btn-secondary', id=self.prefix + '-select-inverse')
            ],
            div(class_='btn-group')[
                button(i(class_='fas fa-trash'), self.delete_label,
                       class_="btn btn-sm btn-danger", id=self.prefix + '-submit-delete',
                       name='_method', value=self.delete_value, type='button')
            ]
        ]

        if self.add:
            button_bar.add(
                div(class_='btn-group')[
                    a(href=self.add[1])[
                        button(self.add[0], type='button', class_='btn btn-sm btn-success')
                    ]
                ]
            )

        if self.others:
            button_bar.add(
                div(class_='btn-group')[self.others]
            )

        if self.hiddens:
            hiddens = div()
            for (k, v) in self.hiddens:
                hiddens.add(
                    literal('<input type="hidden" name="%s" value="%s" />' % (k, v)))
        else:
            hiddens = ''

        sform = form(name=self.name, method='post', action=self.action)
        sform.add(
            div(id=self.prefix + '-modal', class_='modal fade', role='dialog', tabindex='-1'),
            button_bar,
            html,
            hiddens
        )

        return sform, jscode + selection_bar_js % {'prefix': self.prefix}


# text templates

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


# EOF
