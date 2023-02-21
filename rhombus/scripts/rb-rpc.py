#!/usr/bin/env python3

# (c) 2022 Hidayat Trimarsanto <trimarsanto@gmail.com>
# This source code file is distributed under MIT License

# requires the following libraries: tinyrpc, click

import click
from tinyrpc import RPCClient
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol, JSONRPCError
from tinyrpc.transports.http import HttpPostClientTransport


class RPCClientProxy(object):

    def __init__(self, url=None):

        self.rpc_cli = RPCClient(
            JSONRPCProtocol(),
            HttpPostClientTransport(url)
        )
        self.proxy = self.rpc_cli.get_proxy()


__RB_RPC__ = None


def rb_rpc():
    return __RB_RPC__.proxy


@click.group()
@click.option('--debug', default=False)
@click.option('--url', required=True)
def cli(debug, url):
    global __RB_RPC__
    click.echo(f"Debug mode is {'on' if debug else 'off'}")
    click.echo(f'URL is: {url}')
    __RB_RPC__ = RPCClientProxy(url)


@cli.command()
@click.option('--login', required=True)
def generate_token(login):

    import getpass

    passwd = getpass.getpass()
    token = rb_rpc().generate_token(login, passwd)
    click.echo(f'Response is: {token}')


@cli.command()
@click.option('--token', required=True)
def check_token(token):

    response = rb_rpc().check_token(token)
    click.echo(response)


@cli.command()
@click.option('--token', required=True)
def revoke_token(token):

    response = rb_rpc().revoke_token(token)
    click.echo(response)


if __name__ == '__main__':

    try:
        cli()
    except JSONRPCError as exc:
        click.echo(f'RPC Error: {str(exc)}')

# EOF
