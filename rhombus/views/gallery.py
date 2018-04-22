
from rhombus.views import *

@roles( PUBLIC )
def index(request):
    """ input tags gallery """

    static = False

    html = div( div(h3('Input Gallery')))

    eform = form( name='rhombus/gallery', method=POST,
                action='')
    eform.add(
        fieldset(
            input_hidden(name='rhombus-gallery_id', value='00'),
            input_text('rhombus-gallery_text', 'Text Field', value='Text field value'),
            input_text('rhombus-gallery_static', 'Static Text Field', value='Text field static',
                static=True),
            input_textarea('rhombus-gallery_textarea', 'Text Area', value='A text in text area'),
            input_select('rhombus-gallery_select', 'Select', value=2,
            	options = [ (1, 'Opt1'), (2, 'Opt2'), (3, 'Opt3') ]),
            input_select('rhombus-gallery_select-multi', 'Select (Multiple)', value=[2,3],
            	options = [ (1, 'Opt1'), (2, 'Opt2'), (3, 'Opt3') ], multiple=True),
            input_select('rhombus-gallery_select2', 'Select2 (Multiple)', value=[2,4],
            	options = [ (1, 'Opt1'), (2, 'Opt2'), (3, 'Opt3'), (4, 'Opt4'), (5, 'Opt5') ], multiple=True),
            input_select('rhombus-gallery_select2-ajax', 'Select2 (AJAX)'),
            checkboxes('rhombus-gallery_checkboxes', 'Check Boxes',
            	boxes = [ ('1', 'Box 1', True), ('2', 'Box 2', False), ('3', 'Box 3', True)]),
            submit_bar(),
        )
    )

    html.add( div(eform) )
    code = '''
$('#rhombus-gallery_select2').select2();

$('#rhombus-gallery_select2-ajax').select2({
  placeholder: 'Select from AJAX',
  minimumInputLength: 3,
  ajax: {
            url: "%s",
            dataType: 'json',
            data: function(params) { return { q: params.term, g: "@ROLES" }; },
            processResults: function(data, params) { return { results: data }; }
        },
});
''' % request.route_url('rhombus.ek-lookup')

    return render_to_response('rhombus:templates/generics/page.mako',
            { 'content': str(html), 'code': code },
            request = request )