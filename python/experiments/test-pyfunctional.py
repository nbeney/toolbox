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

    def test_distinct(self):
        res = seq(1, 4, 2, 3, 2, 4, 5).distinct()
        assert res == [1, 2, 3, 4, 5]

    def test_distinct_by(self):
        res = seq.range(10).distinct_by(lambda x: x % 3)
        assert res == [0, 1, 2]

    def test_drop(self):
        res = seq.range(10).drop(5)
        assert res == [5, 6, 7, 8, 9]

    def test_drop_right(self):
        res = seq.range(10).drop_right(5)
        assert res == [0, 1, 2, 3, 4]

    def test_drop_while(self):
        res = seq.range(10).drop_while(lambda x: x <= 6)
        assert res == [7, 8, 9]

    def test_enumerate(self):
        res = seq('red', 'green', 'blue').enumerate()
        assert res == [(0, 'red'), (1, 'green'), (2, 'blue')]

        res = seq('red', 'green', 'blue').enumerate(start=1)
        assert res == [(1, 'red'), (2, 'green'), (3, 'blue')]

    def test_filter_or_where(self):
        res = seq.range(10).filter(lambda x: x % 2 == 0)
        assert res == [0, 2, 4, 6, 8]

        res = seq.range(10).where(lambda x: x % 2 == 0)
        assert res == [0, 2, 4, 6, 8]

    def test_filter_not(self):
        res = seq.range(10).filter_not(lambda x: x % 2 == 0)
        assert res == [1, 3, 5, 7, 9]

    def test_init(self):
        res = seq.range(5).init()
        assert res == [0, 1, 2, 3]

    def test_inits(self):
        res = seq.range(5).inits()
        assert res == [[0, 1, 2, 3, 4], [0, 1, 2, 3], [0, 1, 2], [0, 1], [0], []]

    def test_map_or_select(self):
        res = seq.range(5).map(lambda x: x ** 2)
        assert res == [0, 1, 4, 9, 16]

        res = seq.range(5).select(lambda x: x ** 2)
        assert res == [0, 1, 4, 9, 16]

    def test_reverse(self):
        res = seq.range(5).reverse()
        assert res == [4, 3, 2, 1, 0]

    def test_slice(self):
        res = seq.range(10).slice(3, 7)
        assert res == [3, 4, 5, 6]

    def test_sliding(self):
        res = seq.range(5).sliding(size=3)
        assert res == [[0, 1, 2], [1, 2, 3], [2, 3, 4]]

        res = seq.range(10).sliding(size=5, step=3)
        assert res == [[0, 1, 2, 3, 4], [3, 4, 5, 6, 7], [6, 7, 8, 9], [9]]

    def test_sorted(self):
        res = seq(1, 5, 3, 2, 4).sorted()
        assert res == [1, 2, 3, 4, 5]

        res = seq(1, 5, 3, 2, 4).sorted(reverse=True)
        assert res == [5, 4, 3, 2, 1]

        res = seq(1, 5, 3, 2, 4).sorted(key=lambda x: x % 2)
        assert res == [2, 4, 1, 5, 3]

    def test_tail(self):
        res = seq.range(5).tail()
        assert res == [1, 2, 3, 4]

    def test_tails(self):
        res = seq.range(5).tails()
        assert res == [[0, 1, 2, 3, 4], [1, 2, 3, 4], [2, 3, 4], [3, 4], [4], []]

    def test_take(self):
        res = seq.range(5).take(3)
        assert res == [0, 1, 2]

    def test_take_while(self):
        res = seq.range(5).take_while(lambda x: x <= 3)
        assert res == [0, 1, 2, 3]

    def test_zip(self):
        res = seq(1, 2, 3).zip([4, 5, 6])
        assert res == [(1, 4), (2, 5), (3, 6)]

        res = seq(1, 2, 3).zip([4, 5])
        assert res == [(1, 4), (2, 5)]

        res = seq(1, 2).zip([4, 5, 6])
        assert res == [(1, 4), (2, 5)]

    def test_zip_with_index(self):
        res = seq('red', 'green', 'blue').zip_with_index()
        assert res == [('red', 0), ('green', 1), ('blue', 2)]

        res = seq('red', 'green', 'blue').zip_with_index(start=1)
        assert res == [('red', 1), ('green', 2), ('blue', 3)]


class TestActions(unittest.TestCase):
    def test_aggregate(self):
        # func
        res = seq.range(5).aggregate(lambda curr, next: curr + next)
        assert res == 10

        # seed + func
        res = seq.range(5).aggregate(100, lambda curr, next: curr + next)
        assert res == 110

        # seed + func + map
        res = seq.range(5).aggregate(100, lambda curr, next: curr + next, lambda res: 'res={}'.format(res))
        assert res == 'res=110'

    def test_find(self):
        res = seq.range(10).find(lambda x: x > 0 and x % 2 == 0 and x % 3 == 0)
        assert res == 6

        res = seq.range(10).find(lambda x: x > 0 and x % 2 == 0 and x % 7 == 0)
        assert res is None

    def test_head_or_first(self):
        res = seq.range(10).head()
        assert res == 0

        res = seq.range(10).first()
        assert res == 0

    def test_head_option(self):
        res = seq.range(10).head_option()
        assert res == 0

        res = seq([]).head_option()
        assert res is None

    def test_last(self):
        res = seq.range(10).last()
        assert res == 9

    def test_last_option(self):
        res = seq.range(10).last_option()
        assert res == 9

        res = seq([]).last_option()
        assert res is None


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

    def test_exists(self):
        assert not seq.range(1, 10).exists(lambda x: x % 2 == 0 and x % 5 == 0)
        assert seq.range(1, 11).exists(lambda x: x % 2 == 0 and x % 5 == 0)


class TestActions_number(unittest.TestCase):
    def test_average(self):
        assert seq(1, 2, 3).average() == 2
        assert seq(1, 2, 3).average(lambda x: 10 * x) == 20

    def test_count(self):
        res = seq.range(10).count(lambda x: x % 2 == 1)
        assert res == 5

    def test_len_or_size(self):
        res = seq.range(10).len()
        assert res == 10

        res = seq.range(10).size()
        assert res == 10

    def test_max(self):
        res = seq('red', 'green', 'blue').max()
        assert res == 'red'

    def test_max_by(self):
        res = seq('red', 'green', 'blue').max_by(len)
        assert res == 'green'

    def test_min(self):
        res = seq('red', 'green', 'blue').min()
        assert res == 'blue'

    def test_min_by(self):
        res = seq('red', 'green', 'blue').min_by(len)
        assert res == 'red'

    def test_product(self):
        res = seq([]).product()
        assert res == 1

        res = seq.range(1, 5).product()
        assert res == 24

        res = seq.range(1, 5).product(projection=lambda x: 2 * x)
        assert res == 2 ** 4 * 24

    def test_sum(self):
        res = seq([]).sum()
        assert res == 0

        res = seq.range(1, 5).sum()
        assert res == 10

        res = seq.range(1, 5).sum(projection=lambda x: 2 * x)
        assert res == 2 * 10


class TestActions_conversion(unittest.TestCase):
    def test_to_dict(self):
        res = seq([('a', 1), ('b', 2)]).to_dict()
        assert res == {'a': 1, 'b': 2}
        assert res.get(10) is None

        res = seq([('a', 1), ('b', 2)]).to_dict(5)
        assert res == {'a': 1, 'b': 2}
        assert res[10] == 5

    def test_to_list(self):
        res = seq.range(5).to_list()
        assert res == [0, 1, 2, 3, 4]

        res = seq.range(5).to_list(n=3)
        assert res == [0, 1, 2]

    def test_to_set(self):
        res = seq(1, 2, 3, 2, 1).to_set()
        assert res == set([1, 2, 3])

    def test_make_string(self):
        res = seq.range(5).make_string('/')
        assert res == '0/1/2/3/4'

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
