#!/usr/bin/python3

from __future__ import print_function

import unittest
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait


def fib(n):
    return 1 if n <= 1 else fib(n - 2) + fib(n - 1)


INPUT = range(10)
OUTPUT = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]


class TestConcurrentFutures(unittest.TestCase):
    def test_seq(self):
        res = map(fib, INPUT)
        self.assertEqual(OUTPUT, list(res))

    def test_threads(self):
        with ThreadPoolExecutor() as e:
            res = e.map(fib, INPUT)
        self.assertEqual(OUTPUT, list(res))

    def test_procs(self):
        with ProcessPoolExecutor() as e:
            res = e.map(fib, INPUT)
        self.assertEqual(OUTPUT, list(res))

    def test_submit(self):
        with ThreadPoolExecutor() as e:
            futures = [e.submit(fib, _) for _ in INPUT]

        done, not_done = wait(futures, timeout=0)
        self.assertLessEqual(len(done), len(futures))
        self.assertGreaterEqual(len(not_done), 0)

        res = [_.result() for _ in futures]
        self.assertEqual(OUTPUT, list(res))

        done, not_done = wait(futures, timeout=0)
        self.assertEqual(len(done), len(futures))
        self.assertEqual(len(not_done), 0)
