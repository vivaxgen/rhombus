
from .tags import *


class inline_inputs(div):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, class_='form-group form-inline row', **kwargs)


class input_text(input_text):

    def class_value(self):
        return f'col-md-{self.size}'

    def class_label(self):
        return f'col-md-{self.offset} control-label'

    def class_input(self):
        return 'form-control' + (' is-invalid' if self.error else '')

    def as_input(self, value=None, static=False):
        elements = [
            label(self.label, class_=f"{self.class_label()} align-self-start pt-2", for_=self.name),
            div(class_=self.class_value())[
                literal(f"<input type='text' id='{self.id or self.name}' name='{self.name or self.id}' "
                        f"value='{escape(value or self.value)}' class='{self.class_input()}' "
                        f"placeholder='{self.placeholder}' style='width:100%' {self.ro() or static} />"),
                self.help()
            ],
            self.info_text()
        ]
        if not isinstance(self.container, inline_inputs):
            return str(div(class_='form-group form-inline row').add(*elements))
        return '\n'.join(str(e) for e in elements)

    #def __html__(self):
    #    return str(literal(self.as_input()))

# EOF
