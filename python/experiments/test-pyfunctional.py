#!/usr/bin/python3

from __future__ import print_function

import io
import sqlite3
import unittest
from operator import add
from tempfile import NamedTemporaryFile

from functional import seq


def _normalize(text):
    lines = text.strip().split('\n')
    return seq(lines) \
        .map(lambda x: x.strip() + '\n') \
        .reduce(add, '')


def _make_str_file(text):
    content = _normalize(text)
    return io.StringIO(content)


def _make_tmp_file(text):
    content = _normalize(text)
    f = NamedTemporaryFile(mode='w', delete=False)
    print(content, file=f)
    f.seek(0)
    return f.name


class TestStreams_input(unittest.TestCase):
    def test_seq(self):
        res = seq(1, 2, 3, 4, 5).sum()
        assert res == 15

        res = seq([1, 2, 3, 4, 5]).sum()
        assert res == 15

    def test_seq_csv(self):
        f = _make_str_file(u'''
            a,b,c
            11,12,13
            21,22,23
            31,32,33
        ''')
        res = seq.csv(f)
        assert res == [['a', 'b', 'c'], ['11', '12', '13'], ['21', '22', '23'], ['31', '32', '33']]

    def test_seq_csv_dict_reader(self):
        f = _make_str_file(u'''
            a,b,c
            11,12,13
            21,22,23
            31,32,33
        ''')
        res = seq.csv_dict_reader(f)
        assert res == [{'a': '11', 'b': '12', 'c': '13'}, {'a': '21', 'b': '22', 'c': '23'},
                       {'a': '31', 'b': '32', 'c': '33'}]

    def test_seq_json_dict(self):
        f = _make_str_file(u'''{"a": 1, "b": 2, "c": 3}''')
        res = seq.json(f).sorted()
        assert res == [('a', 1), ('b', 2), ('c', 3)]

    def test_seq_json_list(self):
        f = _make_str_file(u'''[1, 2, 3]''')
        res = seq.json(f)
        assert res == [1, 2, 3]

    def test_seq_jsonl(self):
        f = _make_str_file(u'''
            [11, 12, 13]
            [21, 22, 23]
            [31, 32, 33]
        ''')
        res = seq.jsonl(f)
        assert res == [[11, 12, 13], [21, 22, 23], [31, 32, 33]]

    def test_seq_open(self):
        path = _make_tmp_file('''
            red
            green
            blue
        ''')
        res = seq.open(path)
        assert res == ['red\n', 'green\n', 'blue\n', '\n']

    def test_seq_range(self):
        assert seq.range(1, 8, 2) == [1, 3, 5, 7]

    def test_seq_sqlite3(self):
        conn = sqlite3.connect(':memory:')
        c = conn.cursor()
        c.execute('''CREATE TABLE demo (color TEXT, value REAL)''')
        c.execute('''INSERT INTO demo VALUES ('red', 1)''')
        c.execute('''INSERT INTO demo VALUES ('green', 2)''')
        c.execute('''INSERT INTO demo VALUES ('blue', 3)''')
        conn.commit()

        res = seq.sqlite3(conn, 'SELECT * FROM demo')
        assert res == [('red', 1), ('green', 2), ('blue', 3)]


class TestStreams_output(unittest.TestCase):
    pass


class TestTransformations(unittest.TestCase):
    def test_cartesian(self):
        res = seq([1, 2]).cartesian([3, 4])
        assert res == [(1, 3), (1, 4), (2, 3), (2, 4)]

        res = seq([1, 2]).cartesian([3, 4], [5, 6])
        assert res == [(1, 3, 5), (1, 3, 6), (1, 4, 5), (1, 4, 6), (2, 3, 5), (2, 3, 6), (2, 4, 5), (2, 4, 6)]


class TestActions(unittest.TestCase):
    def test_aggregate_func(self):
        # func
        res = seq.range(5).aggregate(lambda curr, next: curr + next)
        assert res == 10

        # seed + func
        res = seq.range(5).aggregate(100, lambda curr, next: curr + next)
        assert res == 110

        # seed + func + map
        res = seq.range(5).aggregate(100, lambda curr, next: curr + next, lambda res: 'res={}'.format(res))
        assert res == 'res=110'


class TestActions_boolean(unittest.TestCase):
    def test_all(self):
        assert seq(True, True).all()
        assert not seq(True, False).all()
        assert not seq(False, False).all()

    def test_any(self):
        assert seq(True, True).any()
        assert seq(True, False).any()
        assert not seq(False, False).all()

    def test_empty(self):
        assert seq([]).empty()
        assert not seq(1, 2, 3).empty()

    def test_non_empty(self):
        assert not seq([]).non_empty()
        assert seq(1, 2, 3).non_empty()


class TestActions_number(unittest.TestCase):
    def test_average(self):
        assert seq(1, 2, 3).average() == 2
        assert seq(1, 2, 3).average(lambda x: 10 * x) == 20

    def test_count(self):
        res = seq.range(10).count(lambda x: x % 2 == 1)
        assert res == 5


class TestActions_conversion(unittest.TestCase):
    def test_to_dict(self):
        res = seq([('a', 1), ('b', 2)]).to_dict()
        assert res == {'a': 1, 'b': 2}
        assert res.get(10) is None

        res = seq([('a', 1), ('b', 2)]).to_dict(5)
        assert res == {'a': 1, 'b': 2}
        assert res[10] == 5

    def test_tabulate(self):
        data = [["Sun", 696000, 1989100000], ["Earth", 6371, 5973.6], ["Moon", 1737, 73.5], ["Mars", 3390, 641.85]]
        expected = '''
            -----  ------  -------------
            Sun    696000     1.9891e+09
            Earth    6371  5973.6
            Moon     1737    73.5
            Mars     3390   641.85
            -----  ------  -------------
        '''
        res = seq(data).tabulate()
        assert _normalize(res) == _normalize(expected)
