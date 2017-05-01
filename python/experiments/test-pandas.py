#!/usr/bin/python3

from __future__ import print_function

import unittest

import numpy as np
import pandas as pd


class TestPandas(unittest.TestCase):
    def test(self):
        df1 = pd.DataFrame([
            ('red', 1),
            ('green', 2),
            ('blue', 3),
        ], columns=['color', 'value'])
        print(df1)
        print()
        df2 = df1[df1.value != 2]
        print(df2)


class TestPandas_Series(unittest.TestCase):
    def test_from_scalar(self):
        s = pd.Series(1)
        self.assertEqual(repr(s.index), 'RangeIndex(start=0, stop=1, step=1)')
        self.assertEqual(repr(s.values), 'array([1], dtype=int64)')
        self.assertEqual(s[0], 1)

    def test_from_scalar_with_index(self):
        s1 = pd.Series(1, index=['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(repr(s1.index), "Index(['a', 'b', 'c', 'd', 'e'], dtype='object')")
        self.assertEqual(repr(s1.values), 'array([1, 1, 1, 1, 1], dtype=int64)')
        self.assertEqual(s1[0], 1)

        s2 = pd.Series(2, index=s1.index)
        self.assertEqual(repr(s2.index), "Index(['a', 'b', 'c', 'd', 'e'], dtype='object')")
        self.assertEqual(repr(s2.values), 'array([2, 2, 2, 2, 2], dtype=int64)')
        self.assertEqual(s2[0], 2)

    def test_from_list(self):
        s = pd.Series([1, 2, 3, 4, 5])
        self.assertEqual(repr(s.index), 'RangeIndex(start=0, stop=5, step=1)')
        self.assertEqual(repr(s.values), 'array([1, 2, 3, 4, 5], dtype=int64)')
        self.assertEqual(s[0], 1)

    def test_from_list_with_index(self):
        s = pd.Series([1, 2, 3, 4, 5], index=['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(repr(s.index), "Index(['a', 'b', 'c', 'd', 'e'], dtype='object')")
        self.assertEqual(repr(s.values), 'array([1, 2, 3, 4, 5], dtype=int64)')
        self.assertEqual(s[0], 1)
        self.assertEqual(s['a'], 1)

    def test_from_dict(self):
        s = pd.Series({'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5})
        self.assertEqual(repr(s.index), "Index(['a', 'b', 'c', 'd', 'e'], dtype='object')")
        self.assertEqual(repr(s.values), 'array([1, 2, 3, 4, 5], dtype=int64)')
        self.assertEqual(s[0], 1)
        self.assertEqual(s['a'], 1)

    def test_len_size_shape_count(self):
        s = pd.Series([1, 2, np.nan, 3, 1])
        self.assertEqual(len(s), 5)
        self.assertEqual(s.size, 5)
        self.assertEqual(s.shape, (5,))
        self.assertEqual(s.count(), 4)  # not nan

    def test_unique(self):
        s = pd.Series([1, 2, 3, np.nan, 1, 2, np.nan, 1, np.nan])
        self.assertEqual(repr(s.unique()), 'array([  1.,   2.,   3.,  nan])')

    def test_value_counts(self):
        s = pd.Series([1, 2, 3, np.nan, 1, 2, np.nan, 1, np.nan])
        vc = s.value_counts()
        self.assertEqual(repr(vc.index), "Float64Index([1.0, 2.0, 3.0], dtype='float64')")
        self.assertEqual(repr(vc.values), 'array([3, 2, 1], dtype=int64)')

    def test_head(self):
        s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(repr(s.head().values), 'array([1, 2, 3, 4, 5], dtype=int64)')
        self.assertEqual(repr(s.head(n=3).values), 'array([1, 2, 3], dtype=int64)')

    def test_tail(self):
        s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(repr(s.tail().values), 'array([ 6,  7,  8,  9, 10], dtype=int64)')
        self.assertEqual(repr(s.tail(n=3).values), 'array([ 8,  9, 10], dtype=int64)')

    def test_take(self):
        s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(repr(s.take([1, 3, 5]).values), 'array([2, 4, 6], dtype=int64)')
