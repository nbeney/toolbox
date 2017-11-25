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

    def test_from_scalar_with_index(self):
        s1 = pd.Series(1, index=['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(repr(s1.index), "Index(['a', 'b', 'c', 'd', 'e'], dtype='object')")
        self.assertEqual(repr(s1.values), 'array([1, 1, 1, 1, 1], dtype=int64)')

        s2 = pd.Series(2, index=s1.index)
        self.assertEqual(repr(s2.index), "Index(['a', 'b', 'c', 'd', 'e'], dtype='object')")
        self.assertEqual(repr(s2.values), 'array([2, 2, 2, 2, 2], dtype=int64)')

    def test_from_list(self):
        s = pd.Series([1, 2, 3, 4, 5])
        self.assertEqual(repr(s.index), 'RangeIndex(start=0, stop=5, step=1)')
        self.assertEqual(repr(s.values), 'array([1, 2, 3, 4, 5], dtype=int64)')

    def test_from_list_with_index(self):
        s = pd.Series([1, 2, 3, 4, 5], index=['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(repr(s.index), "Index(['a', 'b', 'c', 'd', 'e'], dtype='object')")
        self.assertEqual(repr(s.values), 'array([1, 2, 3, 4, 5], dtype=int64)')
        self.assertEqual(s[0], 1)

    def test_from_dict(self):
        s = pd.Series({'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5})
        self.assertEqual(repr(s.index), "Index(['a', 'b', 'c', 'd', 'e'], dtype='object')")
        self.assertEqual(repr(s.values), 'array([1, 2, 3, 4, 5], dtype=int64)')
        self.assertEqual(s[0], 1)

    def test_len_size_shape_count(self):
        s = pd.Series([1, 2, np.nan, 3, 1])
        self.assertEqual(len(s), 5)
        self.assertEqual(s.size, 5)
        self.assertEqual(s.shape, (5,))
        self.assertEqual(s.count(), 4)  # not nan

    def test_unique(self):
        s = pd.Series([1, 2, 3, np.nan, 1, 2, np.nan, 1, np.nan])
        act = s.unique().tolist()
        exp = [1., 2., 3., np.nan]
        self.assertEqual(str(act), str(exp))

    def test_value_counts(self):
        s = pd.Series([3, 2, 1, np.nan, 3, 2, np.nan, 3, np.nan, 3, 2, 1])
        vc = s.value_counts()
        act = list(zip(vc.index, vc.values))
        exp = [(3.0, 4), (2.0, 3), (1.0, 2)]
        self.assertEqual(act, exp)

    def test_head(self):
        s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(s.head().tolist(), [1, 2, 3, 4, 5])
        self.assertEqual(s.head(n=3).tolist(), [1, 2, 3])

    def test_tail(self):
        s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(s.tail().tolist(), [6, 7, 8, 9, 10])
        self.assertEqual(s.tail(n=3).tolist(), [8, 9, 10])

    def test_take(self):
        s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(s.take([1, 3, 5]).tolist(), [2, 4, 6])

    def test_lookup_default_index(self):
        s = pd.Series(['one', 'two', 'three', 'four', 'five'])
        # By index / position
        self.assertEqual(s[1], 'two')
        try:
            s[100] or self.fail('KeyError should have been raised!')
        except KeyError:
            pass
        self.assertEqual(s[[1, 3]].tolist(), ['two', 'four'])
        self.assertEqual(s[[1, 100]].tolist(), ['two', np.nan])

    def test_lookup_str_index(self):
        s = pd.Series(['one', 'two', 'three', 'four', 'five'], index=['a', 'b', 'c', 'd', 'e'])

        # By index
        self.assertEqual(s['a'], 'one')
        try:
            s['xyz'] or self.fail('KeyError should have been raised!')
        except KeyError:
            pass
        self.assertEqual(s[['a', 'c']].tolist(), ['one', 'three'])
        self.assertEqual(s[['a', 'xyz']].tolist(), ['one', np.nan])

        # By position
        self.assertEqual(s[1], 'two')
        try:
            s[100] or self.fail('IndexError should have been raised!')
        except IndexError:
            pass
        self.assertEqual(s[[1, 3]].tolist(), ['two', 'four'])
        try:
            s[[1, 100]] or self.fail('IndexError should have been raised!')
        except IndexError:
            pass

    def test_lookup_int_index(self):
        s = pd.Series(['one', 'two', 'three', 'four', 'five'], index=[1, 2, 3, 4, 5])

        # By index
        self.assertEqual(s[1], 'one')
        self.assertEqual(s[[1, 3]].tolist(), ['one', 'three'])
        self.assertEqual(s.loc[1], 'one')
        try:
            s.loc[100] or self.fail('KeyError should have been raised!')
        except KeyError:
            pass
        self.assertEqual(s.loc[[1, 3]].tolist(), ['one', 'three'])
        self.assertEqual(s.loc[[1, 100]].tolist(), ['one', np.nan])

        # By position
        self.assertEqual(s.iloc[1], 'two')
        try:
            s.iloc[100] or self.fail('IndexError should have been raised!')
        except IndexError:
            pass
        self.assertEqual(s.iloc[[1, 3]].tolist(), ['two', 'four'])
        try:
            s.iloc[[1, 100]] or self.fail('IndexError should have been raised!')
        except IndexError:
            pass

    def test_alignement(self):
        s1 = pd.Series([1, 2, 3, 4, 10], index=['a', 'b', 'c', 'd', 'x'])
        s2 = pd.Series([4, 3, 2, 1, 20], index=['d', 'c', 'b', 'a', 'y'])
        s = s1 + s2
        self.assertEqual(s.index.tolist(), ['a', 'b', 'c', 'd', 'x', 'y'])
        self.assertEqual(str(s.values.tolist()), str([2., 4., 6., 8., np.nan, np.nan]))

    def test_arithmetic_scalar_series(self):
        s1 = pd.Series([1, 2, 3, 4, 5], index=['a', 'b', 'c', 'd', 'e'])
        s2 = 2 * s1
        self.assertEqual(s1.index.tolist(), s2.index.tolist())
        self.assertEqual(s2.values.tolist(), [2, 4, 6, 8, 10])

    def test_arithmetic_series_series(self):
        s1 = pd.Series({'a': 1, 'b': 2, 'c': 3, 'd': 4})
        s2 = pd.Series({'b': 2, 'c': 3, 'd': 4, 'e': 5})
        s3 = s1 + s2
        self.assertEqual(s3.index.tolist(), ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(str(s3.values.tolist()), str([np.nan, 4., 6., 8., np.nan]))

    def test_boolean_selection(self):
        s = pd.Series(np.arange(101))

        values = s[(s % 3 == 0) & (s % 5 == 0) & (s > 0)]
        self.assertEqual(values.tolist(), [15, 30, 45, 60, 75, 90])

        self.assertTrue((s >= 0).all())
        self.assertFalse((s % 2 == 0).all())

        self.assertTrue((s % 2 == 0).any())
        self.assertFalse((s < 0).any())

        self.assertEqual((s % 10 == 0).sum(), 11)

    def test_reindexing_with_index(self):
        s1 = pd.Series([1, 2, 3])
        s2 = pd.Series([4, 5, 6])
        combined = pd.concat([s1, s2])
        self.assertEqual(combined.index.tolist(), [0, 1, 2, 0, 1, 2])
        self.assertEqual(combined.values.tolist(), [1, 2, 3, 4, 5, 6])
        combined.index = np.arange(0, len(combined))
        self.assertEqual(combined.index.tolist(), [0, 1, 2, 3, 4, 5])
        self.assertEqual(combined.values.tolist(), [1, 2, 3, 4, 5, 6])

    def test_reindexing_with_reindex(self):
        s1 = pd.Series(['red', 'green', 'blue'], index=[0, 3, 5])

        s2 = s1.reindex([0, 3, 10])
        self.assertEqual(s2.index.tolist(), [0, 3, 10])
        self.assertEqual(s2.values.tolist(), ['red', 'green', np.nan])

        s3 = s1.reindex([0, 3, 10], fill_value=0)
        self.assertEqual(s3.index.tolist(), [0, 3, 10])
        self.assertEqual(s3.values.tolist(), ['red', 'green', 0])

        s4 = s1.reindex(np.arange(0, 7), method='ffill')
        self.assertEqual(s4.index.tolist(), [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(s4.values.tolist(), ['red', 'red', 'red', 'green', 'green', 'blue', 'blue'])

        s5 = s1.reindex(np.arange(0, 7), method='bfill')
        self.assertEqual(s5.index.tolist(), [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(s5.values.tolist(), ['red', 'green', 'green', 'green', 'blue', 'blue', np.nan])

class TestPandas_Pivot(unittest.TestCase):
    def test_1(self):
        df = pd.read_csv('haircolor.csv')
        df
