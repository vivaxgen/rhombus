__copyright__ = '''
auxtypes.py - Rhombus SQLAlchemy auxiliary types
(c) 2021 Hidayat Trimarsanto <anto@eijkman.go.id> <trimarsanto@gmail.com>

All right reserved.
This software is licensed under LGPL v3 or later version.
Please read the README.txt of this software.
'''

from sqlalchemy import types
from sqlalchemy.dialects.postgresql import base as pg

import uuid
import json
import yaml
import copy


# create universal UUID

class UUID(types.TypeDecorator):
    name = 'rhombus.eijkman.go.id'
    impl = types.BLOB

    def __init__(self):
        types.TypeDecorator.__init__(self, length=16)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(types.BLOB(self.impl.length))
        else:
            return dialect.type_descriptor(pg.UUID())

    @staticmethod
    def _coerce(value):
        if value and not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(value)

            except (TypeError, ValueError):
                value = uuid.UUID(bytes=value)

        return value

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        if not isinstance(value, uuid.UUID):
            value = self._coerce(value)

        if dialect.name == 'postgresql':
            return str(value)

        return value.bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        if dialect.name == 'postgresql':
            if isinstance(value, uuid.UUID):
                return value
        else:
            return uuid.UUID(bytes=value)

    @classmethod
    def new(cls):
        return uuid.uuid3(uuid.NAMESPACE_URL, cls.name)


# create JSON column
# XXX: may be more appropriate to create a dict-based object that will serialize to JSON?

null = object()


class JSONCol(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        if value is null:
            value = None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

    def copy_value(self, value):
        return copy.deepcopy(value)


# create YAML column


class YAMLCol(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        if value is null:
            value = None
        return yaml.dump(value, default_flow_style=True)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return yaml.load(value, yaml.SafeLoader)

    def copy_value(self, value):
        return copy.deepcopy(value)
