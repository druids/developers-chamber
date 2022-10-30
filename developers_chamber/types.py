import datetime
from enum import Enum

from click import Choice, ParamType


class EnumType(Choice):
    def __init__(self, enum):
        self.__enum = enum
        super().__init__(enum.__members__)

    def convert(self, value, param, ctx):
        return self.__enum[super().convert(value, param, ctx)]


class ReleaseType(Enum):

    major = 'major'
    minor = 'minor'
    patch = 'patch'
    build = 'build'

    def __str__(self):
        return self.value


class TimedeltaType(ParamType):
    name = "timedelta"

    _units = dict(d=60 * 60 * 8, h=60 * 60, m=60, s=1)

    def convert(self, value, param, ctx):
        seconds = 0
        default_unit = unit = self._units['h']  # default to hours
        result_value = ''
        for ch in list(str(value).strip()):
            if ch.isdigit():
                result_value += ch
                continue
            if ch in self._units:
                unit = self._units[ch]
                if result_value:
                    seconds += unit * int(result_value)
                    result_value = ''
                    unit = default_unit
                continue
            if ch in ' \t':
                # skip whitespace
                continue
            raise self.fail('Invalid time delta: {}'.format(value))
        if result_value:
            seconds = unit * int(result_value)
        return datetime.timedelta(seconds=seconds)
