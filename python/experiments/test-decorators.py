from __future__ import print_function


def register(name, default=False):
    def wrapper(cls):
        register.map[name] = cls
        if default:
            register.default = name
        return cls

    return wrapper


register.map = {}
register.default = None


@register('aaa')
class A:
    def __init__(self):
        print('__init__', self.__class__.__name__)


@register('bbb', default=True)
class B:
    def __init__(self):
        print('__init__', self.__class__.__name__)


@register('ccc')
class C:
    def __init__(self):
        print('__init__', self.__class__.__name__)


print('register.map.keys ', sorted(register.map.keys()))
print('register.map.items', sorted(register.map.items()))
print('register.default  ', register.default)

register.map[register.default]()
