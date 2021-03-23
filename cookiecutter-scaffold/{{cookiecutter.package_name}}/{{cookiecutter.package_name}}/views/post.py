
## simple example of typical rhombus viewer

from {{cookiecutter.package_name}}.views import *
from rhombus.lib.utils import random_string

class PostViewer(object):

    def __init__(self, request):
        self.request = request
        self.dbh = get_dbhandler()
        self.post = None

    def index( self ):

        content = div()
        self.post = self.dbh.get_post( int(self.request.matchdict.get('id', 0)))

        content.add( h2(self.post.title) )
        content.add( div(self.post.content) )

        return render_to_response('{{cookiecutter.package_name}}:templates/generic_page.mako',
                    {
                        'html': content,
                    }, request = self.request
        )

    @m_roles( PUBLIC )
    def edit( self ):
        pass


    @m_roles( PUBLIC )
    def add( self ):
        req = self.request
        post = self.dbh.Post()

        if req.method == 'POST':

            post.update( self.parse_form(req.params) )
            self.dbh.session().add(post)

            return HTTPFound(location = '/')

        content = div()
        content.add( self.edit_form(post))

        return render_to_response('{{cookiecutter.package_name}}:templates/generic_page.mako',
                    {
                        'html': content,
                    }, request = req
        )


    @m_roles( PUBLIC )
    def action(self):
        pass



    def edit_form(self, post, create=False):
        """ return HTML form populated by post's data """

        dbh = self.dbh
        request = self.request

        eform = form( name='{{cookiecutter.package_name}}/post', method=POST )
        eform.add(

            self.hidden_fields( self.request, post ),

            fieldset(
                multi_inputs(name='{{cookiecutter.package_name}}-group-user-type')[
                input_select('{{cookiecutter.package_name}}-group_id', 'Group', value=post.group_id, offset=1, size=2,
                    options = [ (g.id, g.name) for g in dbh.get_group() ]),
                input_select('{{cookiecutter.package_name}}-user_id', 'User', value=post.user_id, offset=1, size=2,
                    options = [ (u.id, u.login) for u in dbh.get_user(request.user.id).group_users() ]),
                input_select_ek('{{cookiecutter.package_name}}-posttype_id', 'Post type', value=post.posttype_id,
                    parent_ek = dbh.get_ekey('@POSTTYPE'), offset=1, size=2),
                ],
                name='{{cookiecutter.package_name}}.post-header'

            ),

            fieldset(
                input_text('{{cookiecutter.package_name}}-title', 'Title', value=post.title, offset=1),
                input_textarea('{{cookiecutter.package_name}}-content', 'Content', value=post.content, offset=1, size="18x8"),
                name='{{cookiecutter.package_name}}.post-main'
            ),

            fieldset(
                custom_submit_bar(('Save', 'save')).set_hide(False).set_offset(2)
            ),
        )

        return eform


    def hidden_fields(self, request, post=None):
        """ return hidden fields for validating a form """

        post = post or self.post
        return fieldset (
            # stamp is used to check whether a post has been updated since the time it was being fetched
            input_hidden(name='{{cookiecutter.package_name}}-stamp', value='%15f' % post.stamp.timestamp() if post.stamp else -1),

            # a special session key to check whether the user and the post are still the same
            input_hidden(name='{{cookiecutter.package_name}}-sesskey', value=generate_sesskey(request.user.id, post.id)),

            name="{{cookiecutter.package_name}}.post-hidden"
        )


    def parse_form(self, f, d=None):

        d = d or dict()

        d['_stamp_'] = float(f['{{cookiecutter.package_name}}-stamp'])

        if '{{cookiecutter.package_name}}-title' in f:
            d['title'] = f['{{cookiecutter.package_name}}-title']
        if '{{cookiecutter.package_name}}-content' in f:
            d['content'] = f['{{cookiecutter.package_name}}-content']

        if '{{cookiecutter.package_name}}-group_id' in f:
            d['group_id'] = int(f.get('{{cookiecutter.package_name}}-group_id'))
        if '{{cookiecutter.package_name}}-user_id' in f:
            d['user_id'] = int(f.get('{{cookiecutter.package_name}}-user_id'))
        if '{{cookiecutter.package_name}}-posttype_id' in f:
            d['posttype_id'] = int(f.get('{{cookiecutter.package_name}}-posttype_id'))

        return d





def list_posts( request ):

    dbh = get_dbhandler()

    posts = dbh.get_posts()

    content = div()
    content.add(
                a('+ New post', class_='btn btn-success',
                    href=request.route_url('post-add')
                ),
            )

    if len(posts) == 0:
        content.add( div("No posts!"))
        return content

    body = tbody()

    #raise RuntimeError

    for post in posts:
        body.add(
            tr(
                td( a(post.title, href=request.route_url('post-view', id=post.id)) ),
            )
        )

    table_posts = table(
        thead(
            tr(
                th('Title')
            )
        )
    )

    table_posts.add( body )

    content.add( table_posts)
    return content


def generate_sesskey(user_id, post_id=None):
    if post_id:
        post_id_part = '%08x' % post_id
    else:
        post_id_part = 'XXXXXXXX'

    return '%08x%s%s' % (user_id, random_string(8), post_id_part)
