#!/usr/bin/python3

from __future__ import print_function

from time import clock


class Chronometer:
    __slots__ = ['_t0', 'duration']

    def __enter__(self):
        self._t0 = clock()
        return self

    def __exit__(self, *exc):
        self.duration = clock() - self._t0
