#!/usr/bin/python3

from __future__ import print_function

import unittest

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
