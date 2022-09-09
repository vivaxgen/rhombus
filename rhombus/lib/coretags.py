#
# this module defines html tags, clean up version that are indepdent
# of css frameworks

from webhelpers2.html import escape, url_escape, literal

GET, POST, PUT, DELETE = 'GET', 'POST', 'PUT', 'DELETE'
FORM_URLENCODED = 'application/x-www-form-urlencoded'
FORM_MULTIPART = 'multipart/form-data'

br = literal('<br/>')
hr = literal('<hr/>')


class htmltag(object):

    def __init__(self, **kwargs):

        self.set_name(kwargs.get('name', '').strip())
        self.set_id(kwargs.get('id', '').strip())
        self.class_ = escape(kwargs.get('class_', ''))

        # root container that holds all tag where this tag reside
        self.container = None

        # content contains all direct htmltag children as list
        self.contents = []

        # elements contains all htmltag under this tag, keyed using name
        self.elements = {}

        # is this tag enabled?
        self.enabled = True

        # is this tag hidden?
        self.hidden = False

        self.attrs = {}
        for (key, val) in kwargs.items():
            key = key.lower()
            if key in ['name', 'class_', 'id']:
                continue
            self.attrs[key.removesuffix('_')] = val

    def r(self) -> str:
        """ render string """
        # this method should be implemented in each corresponding derived class
        raise NotImplementedError()

    def __str__(self):
        """ return printable string information about the tag """
        return f'<{self.__class__.__name__} {self.name or self.id or "?"}>'

    def __repr__(self):
        """ return detailed information about this tag """
        return f"{self.__class__.__name__}(name='{self.name}', id='{self.id}', class='{self.class_}')"

    def __call__(self):
        raise NotImplementedError()

    def __html__(self):
        """ return html string, used by mako rendering system """
        return literal(self.r())

    def __contains__(self, identifier):
        return identifier in self.elements

    def __iadd__(self, element):
        return self.add(element)

    def add(self, *elements, autoregister=True):
        for element in elements:
            self.contents.append(element)
            if autoregister:
                self.register_element(element)
        return self

    def __getitem__(self, arg):
        if type(arg) in [tuple, list]:
            self.add(* list(arg))
        else:
            self.add(arg)
        return self

    def attributes(self, attrs_only=False):
        """ attrs_only means name and/or id are not returned """
        attrs = []

        if not attrs_only:

            if self.name or self.id:
                attrs.append(f'name="{escape(self.name or self.id)}" '
                             f'id="{escape(self.id or self.name)}"')
            if self.class_:
                attrs.append(f'class="{escape(self.class_)}"')

        for (key, val) in self.attrs.items():
            if val is True:
                attrs.append(escape(key))
            elif not (val is None or val is False):
                attrs.append(f'{escape(key)}="{escape(val)}"')

        return ' '.join(attrs)

    def set_name(self, name):
        self.name = name

    def set_id(self, id):
        self.id = id or self.name

    def enable(self, flag=True):
        self.enabled = flag

    def get(self, identifier):
        return self.elements[identifier]

    def insert(self, index, *elements):
        for element in reversed(elements):
            self.contents.insert(index, element)
            self.register_element(element)
        return self

    def register_element(self, el):
        root = self.get_container()
        if not isinstance(el, htmltag):
            return
        if (identifier := el.id):
            if identifier in root.elements:
                raise RuntimeError(f'duplicate element id/name: {identifier}')
            root.elements[identifier] = el
        for (identifier, value) in el.elements.items():
            if identifier in root.elements:
                raise RuntimeError(f'duplicate element id/name: {identifier}')
            root.elements[identifier] = value
        el.container = self

    def get_container(self):
        """ if self.container is None, we are the root container """
        return self.container.get_container() if self.container else self

    def r_contents(self, elements=None):
        return '\n'.join(
            (c.r() if isinstance(c, htmltag) else escape(c)) for c in (elements or self.contents))


class singletag(htmltag):
    _t = ''

    def __init__(self, *args, autoregister=True, **kwargs):
        super().__init__(**kwargs)
        self.add(*args, autoregister=autoregister)

    def r(self):
        return f'<{self._t} {self.attributes()} />'


class image(singletag):
    _t = 'image'


class inputtag(singletag):
    _t = 'input'


class doubletag(singletag):
    _t = ''

    def r(self):
        return (
            f'<{self._t} {self.attributes()}>'
            f'{self.r_contents()}'
            f'</{self._t}>\n'
        )


class div(doubletag):
    _t = 'div'


class span(doubletag):
    _t = 'span'


class h1(doubletag):
    _t = 'h1'


class h2(doubletag):
    _t = 'h2'


class h3(doubletag):
    _t = 'h3'


class h4(doubletag):
    _t = 'h4'


class h5(doubletag):
    _t = 'h5'


class h6(doubletag):
    _t = 'h6'


class p(doubletag):
    _t = 'p'


class a(doubletag):
    _t = 'a'


class b(doubletag):
    _t = 'b'


class i(doubletag):
    _t = 'i'


class pre(doubletag):
    _t = 'pre'


class label(doubletag):
    _t = 'label'


class fieldset(doubletag):
    _t = 'fieldset'


class textareatag(doubletag):
    _t = 'textarea'


class selecttag(doubletag):
    _t = 'select'


class optiontag(doubletag):
    _t = 'option'


# lists and definitions

class ul(doubletag):
    _t = 'ul'

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.add(*args)

    def add(self, *args, autoregister=None):
        """ autoregister is not used, just for placeholder """
        for arg in args:
            if not isinstance(arg, li) and arg != '':
                raise ValueError(f'UL/OL should only have LI content, not {arg}')
            self.contents.append(arg)


class ol(ul):
    _t = 'ol'


class li(doubletag):
    _t = 'li'


class dl(doubletag):
    _t = 'dl'


class dt(doubletag):
    _t = 'dt'


class dd(doubletag):
    _t = 'dd'


# button

class button(doubletag):
    _t = 'button'


# tables

class table(doubletag):
    _t = 'table'


class thead(doubletag):
    _t = 'thead'


class tbody(doubletag):
    _t = 'tbody'


class tr(doubletag):
    _t = 'tr'


class th(doubletag):
    _t = 'th'


class td(doubletag):
    _t = 'td'


# others

class nav(doubletag):
    _t = 'nav'


class footer(doubletag):
    _t = 'footer'

# EOF
