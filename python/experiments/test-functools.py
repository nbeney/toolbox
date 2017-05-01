#!/usr/bin/python3

from __future__ import print_function

import unittest
from functools import lru_cache, total_ordering, partialmethod, singledispatch, wraps
from functools import partial
from functools import reduce
from math import log
from operator import add
from timeit import timeit


def fib_norm(n):
    return 1 if n in (0, 1) else fib_norm(n - 2) + fib_norm(n - 1)


@lru_cache()
def fib_cached(n):
    return 1 if n in (0, 1) else fib_cached(n - 2) + fib_cached(n - 1)


class TestFunctools(unittest.TestCase):
    def test_lrucache(self):
        self.assertEqual(89, fib_norm(10))
        self.assertEqual(fib_norm(10), fib_cached(10))
        N = 10000
        norm = timeit('fib_norm(10)', number=N, globals=globals())
        cached = timeit('fib_cached(10); fib_cached.cache_clear()', number=N, globals=globals())
        print(norm, 'vs', cached)
        self.assertGreater(norm, cached)

    def test_total_ordering(self):
        @total_ordering  # Does not seem to make a difference in Python 3.6
        class C1:
            def __init__(self, x):
                self.x = x

            def __str__(self):
                return 'C1({})'.format(self.x)

            def __eq__(self, other):
                return self.x == other.x

            def __lt__(self, other):
                return self.x < other.x

        a = C1(10)
        b = C1(20)
        self.assertLess(a, b)
        self.assertGreater(b, a)

    def test_partial(self):
        inc = partial(add, 1)
        self.assertEqual(3, inc(2))

    def test_partialmethod(self):
        class Cell(object):
            def __init__(self):
                self._alive = False

            @property
            def alive(self):
                return self._alive

            def set_state(self, state):
                self._alive = bool(state)

            set_alive = partialmethod(set_state, True)
            set_dead = partialmethod(set_state, False)

        c = Cell()
        self.assertFalse(c.alive)
        c.set_alive()
        self.assertTrue(c.alive)
        c.set_dead()
        self.assertFalse(c.alive)

    def test_reduce(self):
        res = reduce(lambda x, y: '({} + {})'.format(x, y), [1, 2, 3])
        self.assertEquals('((1 + 2) + 3)', res)
        res = reduce(lambda x, y: '({} + {})'.format(x, y), [1, 2, 3], 0)
        self.assertEquals('(((0 + 1) + 2) + 3)', res)

    def test_singledispatch(self):
        @singledispatch
        def fun(arg):
            return 'no override: {}'.format(arg)

        @fun.register(bool)
        def fun_str(arg):
            return 'bool override: {}'.format(arg)

        @fun.register(str)
        def fun_str(arg):
            return 'str override: {}'.format(arg)

        @fun.register(int)
        @fun.register(float)
        def fun_int_float(arg):
            return 'number override: {}'.format(arg)

        self.assertEqual('str override: hello', fun('hello'))
        self.assertEqual('bool override: True', fun(True))
        self.assertEqual('number override: 1', fun(1))
        self.assertEqual('number override: 1.0', fun(1.0))
        self.assertEqual('no override: [1, 2, 3]', fun([1, 2, 3]))

    def test_wraps(self):
        def nullable_unwrapped(func):
            def wrapped_func(arg):
                return None if arg is None else func(arg)

            return wrapped_func

        nlog_unwrapped = nullable_unwrapped(log)

        self.assertEqual(0, nlog_unwrapped(1))
        self.assertEqual(None, nlog_unwrapped(None))
        self.assertNotEqual(log.__name__, nlog_unwrapped.__name__)
        self.assertNotEqual(log.__doc__, nlog_unwrapped.__doc__)

        def nullable_wrapped(func):
            @wraps(func)
            def wrapped_func(arg):
                return None if arg is None else func(arg)

            return wrapped_func

        nlog_wrapped = nullable_wrapped(log)

        self.assertEqual(0, nlog_wrapped(1))
        self.assertEqual(None, nlog_wrapped(None))
        self.assertEqual(log.__name__, nlog_wrapped.__name__)
        self.assertEqual(log.__doc__, nlog_wrapped.__doc__)
