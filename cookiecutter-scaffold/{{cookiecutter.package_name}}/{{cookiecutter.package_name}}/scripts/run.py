
import sys, os
import argparse

from rhombus.scripts.run import main as rhombus_main, set_config
from rhombus.lib.utils import cout, cerr, cexit

from {{cookiecutter.package_name}}.models.handler import DBHandler

def greet():
    cerr('command line utility for {{cookiecutter.project_name}}')


def usage():
    cerr('{{cookiecutter.package_name}}-run - command line utility for {{cookiecutter.project_name}}')
    cerr('usage:')
    cerr('\t%s scriptname [options]' % sys.argv[0])
    sys.exit(0)


set_config( environ='RHOMBUS_CONFIG',
            paths = ['{{cookiecutter.package_name}}.scripts.'],
            greet = greet,
            usage = usage,
            dbhandler_class = DBHandler,
            includes = ['{{cookiecutter.package_name}}.includes'],
)

main = rhombus_main



