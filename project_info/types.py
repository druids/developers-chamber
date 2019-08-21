from enum import Enum

from click import Choice


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
