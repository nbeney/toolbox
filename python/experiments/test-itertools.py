#!/usr/bin/python3

from __future__ import print_function

import unittest
from itertools import count, islice, cycle, repeat, accumulate, chain, combinations, combinations_with_replacement, \
    compress
from operator import add


class TestItertools_infinite(unittest.TestCase):
    def test_count(self):
        res = count(1)
        self.assertEqual([1, 2, 3], list(islice(res, 0, 3)))
        res = count(1, 2)
        self.assertEqual([1, 3, 5], list(islice(res, 0, 3)))

    def test_cycle(self):
        res = cycle('ABC')
        self.assertEqual(['A', 'B', 'C', 'A', 'B', 'C'], list(islice(res, 0, 6)))

    def test_repeat(self):
        res = repeat(1)
        self.assertEqual([1, 1, 1, 1, 1], list(islice(res, 0, 5)))
        res = repeat(1, 3)
        self.assertEqual([1, 1, 1], list(islice(res, 0, 5)))


class TestItertools_finite(unittest.TestCase):
    def test_accumulate(self):
        res = accumulate([3, 4, 6, 2, 1, 9, 0, 7, 5, 8])
        self.assertEqual([3, 7, 13, 15, 16, 25, 25, 32, 37, 45], list(res))
        res = accumulate([3, 4, 6, 2, 1, 9, 0, 7, 5, 8], add)
        self.assertEqual([3, 7, 13, 15, 16, 25, 25, 32, 37, 45], list(res))
        res = accumulate([3, 4, 6, 2, 1, 9, 0, 7, 5, 8], max)
        self.assertEqual([3, 4, 6, 6, 6, 9, 9, 9, 9, 9], list(res))

    def test_chain(self):
        res = chain('ABC', 'D', 'EF')
        self.assertEqual(['A', 'B', 'C', 'D', 'E', 'F'], list(res))

    def test_compress(self):
        res = compress('ABCDEF', [1, 1, 0, 0, 1, 1])
        self.assertEqual(['A', 'B', 'E', 'F'], list(res))


class TestItertools_combinatoric(unittest.TestCase):
    def test_combinations(self):
        res = combinations('ABCD', 2)
        self.assertEqual(['AB', 'AC', 'AD', 'BC', 'BD', 'CD'], [''.join(_) for _ in res])
        res = combinations('ABCD', 3)
        self.assertEqual(['ABC', 'ABD', 'ACD', 'BCD'], [''.join(_) for _ in res])

    def test_combinations_with_replacement(self):
        res = combinations_with_replacement('ABC', 2)
        self.assertEqual(['AA', 'AB', 'AC', 'BB', 'BC', 'CC'], [''.join(_) for _ in res])
        res = combinations_with_replacement('ABC', 2)
        self.assertEqual(['AA', 'AB', 'AC', 'BB', 'BC', 'CC'], [''.join(_) for _ in res])
