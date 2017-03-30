import re
from werkzeug.routing import BaseConverter

class BasenameConverter(BaseConverter):

    def to_python(self, value):
        return BasenameConverter._check_and_return_value(value)

    def to_url(self, values):
        return BasenameConverter(value)

    @staticmethod
    def _check_and_return_value(value):
        if not isinstance(value, str):
            return None
        if not len(value) == 32:
            return None
        if re.fullmatch('^[a-z0-9]{32}$', value) is None:
            return None
        return value
