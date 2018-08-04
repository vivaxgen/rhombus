import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()

requires = [
    'SQLAlchemy',
    'zope.sqlalchemy',
    'transaction',
    'dogpile.cache',
    'pyramid',
    'pyramid_mako',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'waitress',
    'PyYAML',
    'passlib',
    'webhelpers2',
    'pyramid_exclog',
    'requests',
    ]

setup(name='rhombus',
      version='0.01',
      description='rhombus',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='rhombus',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = rhombus:main
      [console_scripts]
      rhombus-run = rhombus.scripts.run:main

      [pyramid.scaffold]
      rhombus = rhombus.scaffolds:RhombusTemplate
      """,
      )
