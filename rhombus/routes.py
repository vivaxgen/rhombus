
from pyramid.session import SignedCookieSessionFactory

from rhombus.lib.utils import cerr, random_string
from rhombus.lib import exceptions as exc
from rhombus.models.fileattach import FileAttachment
from rhombus.views import generics
from rhombus import configkeys as ck


def includeme(config):

    cerr('rhombus configuration with prefix: %s' % config.route_prefix)

    # configure exception handler view
    config.add_exception_view(generics.autherror_page, exc.AuthError)

    config.include('pyramid_mako')
    config.add_static_view(name='rhombus_static', path="rhombus:static/")

    session_factory = SignedCookieSessionFactory(random_string(64))
    config.set_session_factory(session_factory)

    # configure RbRequest

    settings = config.get_settings()

    # configure exception views if debugtoolbar is not enabled
    if 'debugtoolbar.includes' not in settings:
        cerr('WARN: setting up in full deployment configuration!')
        config.add_view('rhombus.views.generics.autherror_page', context=PermissionError)
        config.add_view('rhombus.views.generics.usererror_page', context=RuntimeError)
        config.add_view('rhombus.views.generics.syserror_page', context=Exception)

    # configure file attachment root
    FileAttachment.set_root_storage_path(settings[ck.rb_attachment_root])
    FileAttachment.set_max_dbsize(int(settings[ck.rb_attachment_maxdbsize]))

    # configure routes & views

    # rpc
    config.include('pyramid_rpc.jsonrpc')
    include_rpc(config)

    if config.route_prefix:
        config.add_route('rhombus.dashboard', '/')
    else:
        config.add_route('rhombus.dashboard', '/dashboard')
    config.add_view('rhombus.views.dashboard.index', route_name='rhombus.dashboard')

    add_route_view(
        config, 'rhombus.views.group', 'rhombus.group',
        '/group',
        '/group/@@action',
        '/group/@@user_action',
        '/group/@@role_action',
        ('/group/@@lookup', 'lookup', 'json'),
        '/group/{id}@@edit',
        '/group/{id}@@save',
        ('/group/{id}', 'view'),
    )

    add_route_view(
        config, 'rhombus.views.ek', 'rhombus.ek',
        '/ek',
        '/ek/@@action',
        ('/ek/@@lookup', 'lookup', 'json'),
        '/ek/{id}@@edit',
        '/ek/{id}@@save',
        ('/ek/{id}', 'view'),
    )

    add_route_view_class(
        config, 'rhombus.views.userclass.UserClassViewer', 'rhombus.userclass',
        '/userclass',
        '/userclass/@@action',
        '/userclass/@@add',
        '/userclass/{id}@@edit',
        ('/userclass/{id}', 'view'),
    )

    add_route_view_class(
        config, 'rhombus.views.user.UserViewer', 'rhombus.user',
        '/user',
        '/user/@@action',
        '/user/@@passwd',
        ('/user/@@lookup', 'lookup', 'json'),
        '/user/@@add',
        '/user/{id}@@edit',
        # '/user/{id}@@passwd',
        ('/user/{id}', 'view'),
    )

    add_route_view(
        config, 'rhombus.views.gallery', 'rhombus.gallery',
        '/gallery',
    )

    # for overriding assets
    override_assets(
        config, settings,
        [
            (ck.override_loginpage, 'rhombus:templates/login.mako'),
        ]
    )

    if ck.override_assets in settings:
        assets = settings['override.assets']
        for asset in assets.split('\n'):
            if not asset:
                continue
            asset_pair = [a.strip() for a in asset.split('>')]
            print('overriding: %s >> %s' % (asset_pair[0], asset_pair[1]))
            config.override_asset(asset_pair[0], asset_pair[1])


def add_route_view(config, view_module, prefix_name, *routelist):
    for route_args in routelist:
        renderer = None
        if type(route_args) == str:
            url = route_args
            if '@@' in route_args:
                view_name = route_args.split('@@')[-1]
                route_name = '%s-%s' % (prefix_name, view_name)
            else:
                view_name = 'index'
                route_name = prefix_name
        else:
            url = route_args[0]
            view_name = route_args[1]
            route_name = '%s-%s' % (prefix_name, view_name)
            if len(route_args) > 2:
                renderer = route_args[2]

        config.add_route(route_name, url)
        config.add_view(
            '%s.%s' % (view_module, view_name),
            route_name=route_name,
            renderer=renderer
        )


def add_route_view_class(config, view_class, prefix_name, *routelist):
    for route_args in routelist:
        renderer = None
        if type(route_args) == str:
            url = route_args
            if '@@' in route_args:
                view_name = route_args.split('@@')[-1]
                route_name = '%s-%s' % (prefix_name, view_name)
            else:
                view_name = 'index'
                route_name = prefix_name
        else:
            url = route_args[0]
            view_name = route_args[1]
            route_name = '%s-%s' % (prefix_name, view_name)
            if len(route_args) > 2:
                renderer = route_args[2]

        config.add_route(route_name, url)
        config.add_view(
            view_class,
            attr=view_name,
            route_name=route_name,
            renderer=renderer
        )


def override_assets(config, settings, asset_list):
    """ asset_list: [ (cfg, asset, def_overrider), ...]
                eg. [ ('override.base', 'rhombus:templates/base.mako',
                        'rhombus:templates/my_base.mako') ]
                with override.base as optional tag in config file, so that asset can also
                be override using config file
    """

    for cfg, asset in asset_list:
        override = settings.get(cfg, asset)
        if override == asset:
            continue
        print("Overriding asset [%s] with [%s]" % (asset, override))
        config.override_asset(
            to_override=asset,
            override_with=override
        )


# rpc mounting

def include_rpc(config):

    config.add_jsonrpc_endpoint('rpc-rb-v1', '/rpc/v1')
    config.add_jsonrpc_method('rhombus.lib.rpc.generate_token', endpoint='rpc-rb-v1', method='generate_token')
    config.add_jsonrpc_method('rhombus.lib.rpc.check_token', endpoint='rpc-rb-v1', method='check_token')
    config.add_jsonrpc_method('rhombus.lib.rpc.revoke_token', endpoint='rpc-rb-v1', method='revoke_token')

# EOF
