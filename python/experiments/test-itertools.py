#!/usr/bin/python3

from __future__ import print_function

import unittest
from itertools import count, islice, cycle, repeat, accumulate, chain, combinations, combinations_with_replacement, \
    compress, dropwhile, filterfalse, groupby, permutations, product, starmap, takewhile, tee, zip_longest
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

    def test_dropwhile(self):
        res = dropwhile(lambda x: x < 'D', 'ABCDEF')
        self.assertEqual(['D', 'E', 'F'], list(res))

    def test_filterfalse(self):
        res = filter(lambda x: x % 2 == 0, [1, 2, 3, 4, 5, 6])
        self.assertEqual([2, 4, 6], list(res))
        res = filterfalse(lambda x: x % 2 == 0, [1, 2, 3, 4, 5, 6])
        self.assertEqual([1, 3, 5], list(res))

    def test_groupby_with_key(self):
        raw_data = ['red', 'green', 'blue', 'orange', 'violet', 'yellow', 'white', 'black']
        sorted_data = sorted(raw_data, key=len)
        res = groupby(sorted_data, len)
        exp = {3: ['red'], 4: ['blue'], 5: ['green', 'white', 'black'], 6: ['orange', 'violet', 'yellow']}
        act = {k: list(g) for k, g in res}
        self.assertEqual(exp, act)

    def test_groupby_without_key(self):
        raw_data = ['red', 'green', 'blue', 'orange', 'red', 'green']
        sorted_data = sorted(raw_data)
        res = groupby(sorted_data)
        exp = {'blue': ['blue'], 'green': ['green', 'green'], 'orange': ['orange'], 'red': ['red', 'red']}
        act = {k: list(g) for k, g in res}
        self.assertEqual(exp, act)

    def test_islice(self):
        res = islice([1, 2, 3, 4, 5], 3)
        self.assertEqual([1, 2, 3], list(res))
        res = islice([1, 2, 3, 4, 5], 2, 4)
        self.assertEqual([3, 4], list(res))
        res = islice([1, 2, 3, 4, 5], 0, 3, 2)
        self.assertEqual([1, 3], list(res))

    def test_starmap(self):
        res = starmap(add, [(1, 2), (3, 4), (5, 6)])
        self.assertEqual([3, 7, 11], list(res))

    def test_takewhile(self):
        res = takewhile(lambda x: x < 'D', 'ABCDEF')
        self.assertEqual(['A', 'B', 'C'], list(res))

    def test_tee(self):
        def gen():
            yield 1
            yield 2
            yield 3

        s = gen()
        itr1, itr2, itr3 = s, s, s
        self.assertEqual([1, 2, 3], list(itr1))
        self.assertEqual([], list(itr2))
        self.assertEqual([], list(itr3))

        s = gen()
        itr1, itr2, itr3 = tee(s, 3)
        self.assertEqual([1, 2, 3], list(itr1))
        self.assertEqual([1, 2, 3], list(itr2))
        self.assertEqual([1, 2, 3], list(itr3))

    def test_zip_longest(self):
        res = zip('ABCDEF', 'xyz')
        self.assertEqual([('A', 'x'), ('B', 'y'), ('C', 'z')], list(res))
        res = zip_longest('ABCDEF', 'xyz')
        self.assertEqual([('A', 'x'), ('B', 'y'), ('C', 'z'), ('D', None), ('E', None), ('F', None)], list(res))
        res = zip_longest('ABCDEF', 'xyz', fillvalue='?')
        self.assertEqual([('A', 'x'), ('B', 'y'), ('C', 'z'), ('D', '?'), ('E', '?'), ('F', '?')], list(res))


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

    def test_permutations(self):
        res = permutations('ABC')
        self.assertEqual(['ABC', 'ACB', 'BAC', 'BCA', 'CAB', 'CBA'], [''.join(_) for _ in res])
        res = permutations('ABC', 1)
        self.assertEqual(['A', 'B', 'C'], [''.join(_) for _ in res])
        res = permutations('ABC', 2)
        self.assertEqual(['AB', 'AC', 'BA', 'BC', 'CA', 'CB'], [''.join(_) for _ in res])

    def test_product(self):
        res = product('ABC')
        self.assertEqual(['A', 'B', 'C'], [''.join(_) for _ in res])
        res = product('ABC', 'ABC')
        self.assertEqual(['AA', 'AB', 'AC', 'BA', 'BB', 'BC', 'CA', 'CB', 'CC'], [''.join(_) for _ in res])
        res = product('ABC', repeat=2)
        self.assertEqual(['AA', 'AB', 'AC', 'BA', 'BB', 'BC', 'CA', 'CB', 'CC'], [''.join(_) for _ in res])
        res = product('ABC', 'xyz')
        self.assertEqual(['Ax', 'Ay', 'Az', 'Bx', 'By', 'Bz', 'Cx', 'Cy', 'Cz'], [''.join(_) for _ in res])
