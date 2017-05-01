#!/usr/bin/python3

from __future__ import print_function

import io
import sys
import unittest
from contextlib import contextmanager, closing, suppress, redirect_stdout, redirect_stderr
from time import clock, sleep
from unittest.mock import MagicMock, call, patch


class TestContextLib(unittest.TestCase):
    @patch('builtins.print')
    def test_contextmanager(self, mock_print):
        @contextmanager
        def trace(name):
            print('>>> {}'.format(name))
            yield
            print('<<< {}'.format(name))

        with trace('xxx'):
            print('test')

        mock_print.assert_has_calls([call('>>> xxx'), call('test'), call('<<< xxx')])

    def test_closing(self):
        with closing(MagicMock()) as obj:
            pass
        obj.close.assert_called_once_with()

    def test_suppress(self):
        with suppress(FileNotFoundError):
            open('some non-existent file')

    def test_redirect_stdout(self):
        f = io.StringIO()
        with redirect_stdout(f):
            print('test')
        self.assertEqual('test\n', f.getvalue())

    def test_redirect_stderr(self):
        f = io.StringIO()
        with redirect_stderr(f):
            print('test', file=sys.stderr)
        self.assertEqual('test\n', f.getvalue())

    def test_ContextManagerClass(self):
        class Chronometer:
            __slots__ = ['_t0', 'duration']

            def __enter__(self):
                self._t0 = clock()
                return self

            def __exit__(self, *exc):
                self.duration = clock() - self._t0

        with Chronometer() as c:
            sleep(1)
        self.assertAlmostEqual(c.duration, 1, places=2)
