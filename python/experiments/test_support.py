from __future__ import print_function

import os
import unittest
from io import StringIO

from click.testing import CliRunner

from support import *

PERSONS_1 = [
    ('xxx', 'Mr X', 1, ''),
]

PERSONS_2 = PERSONS_1 + [
    ('yyy', 'Mr Y', 2, 'Tue Thu'),
]

PERSONS_3 = PERSONS_2 + [
    ('zzz', 'Mr Z', 3, 'Fri'),
]

DATES_1 = [
    ('20171127', 'Mon', 'xxx', '', ''),
]

DATES_2 = DATES_1 + [
    ('20171128', 'Tue', 'yyy', 'xxx zzz', ''),
]

DATES_3 = DATES_2 + [
    ('20171129', 'Wed', 'zzz', '', 'xxx yyy'),
]


def make_input_file(persons, dates):
    cc = '''
# Comment line 1
# Comment line 2
    '''

    pp = ['|'.join(str(_) for _ in p) for p in persons]
    pp = '''
PERSON | NAME           | INITIAL_SCORE | RECURRING_WFH_DAYS
-------|----------------|---------------|-------------------
    ''' + '\n'.join(pp)

    dd = ['|'.join(str(_) for _ in d) for d in dates]
    dd = '''
DATE     | DOW | ONCALL | UNAVAILABLE | HOLIDAYS
---------|-----|--------|-------------|---------
    ''' + '\n'.join(dd)

    return StringIO(cc + pp + dd)


def file_line_count(path):
    with open(path, 'r') as f:
        return len([None for _ in f if not (_.strip() == '' or _.startswith('#') or _.startswith('--'))])


def file_contains(path, text):
    with open(path, 'r') as f:
        return any(text in _ for _ in f)


# class TestEngine(unittest.TestCase):
#     def test_last_oncall_date_from_empty(self):
#         _reinit_pdl(make_input_file([], []))
#         LastDate = pdl.Variable('Last Date')
#         res = support.last_oncall_date(LastDate) & (LastDate != DUMMY_DATE)
#         self.assertEqual(res, [])
#
#     def test_last_oncall_date_from_one(self):
#         _reinit_pdl(make_input_file([], [('20171129', None, 'xxx', None, None)]))
#         LastDate = pdl.Variable('Last Date')
#         res = support.last_oncall_date(LastDate) & (LastDate != DUMMY_DATE)
#         self.assertEqual(res[0][0], '20171129')
#
#     def test_last_oncall_date_from_many(self):
#         _reinit_pdl(make_input_file([], DATES_3))
#         LastDate = pdl.Variable('Last Date')
#         res = support.last_oncall_date(LastDate) & (LastDate != DUMMY_DATE)
#         self.assertEqual(res[0][0], '20171129')
#
#     def test_next_oncall_date_from_empty(self):
#         _reinit_pdl(make_input_file([], []))
#         NextDate = pdl.Variable('Next Date')
#         res = support.next_oncall_date(NextDate) & (NextDate != DUMMY_DATE)
#         self.assertEqual(res, [])
#
#     def test_next_oncall_date_from_one(self):
#         _reinit_pdl(make_input_file([], [('20171129', None, 'xxx', None, None)]))
#         NextDate = pdl.Variable('Next Date')
#         res = support.next_oncall_date(NextDate) & (NextDate != DUMMY_DATE)
#         self.assertEqual(res[0][0], '20171130')
#
#     def test_next_oncall_date_from_many(self):
#         _reinit_pdl(make_input_file([], DATES_3))
#         NextDate = pdl.Variable('Next Date')
#         res = support.next_oncall_date(NextDate) & (NextDate != DUMMY_DATE)
#         self.assertEqual(res[0][0], '20171130')


class TestRota_Core(unittest.TestCase):
    def test_new(self):
        r = Rota()
        self.assertEqual(len(r), 0)

    def test_seggregation(self):
        a = Rota().load(make_input_file(persons=PERSONS_1, dates=DATES_1))
        b = Rota().load(make_input_file(persons=PERSONS_2, dates=DATES_2))
        self.assertEqual(len(a), len(DATES_1))
        self.assertEqual(a.persons(), PERSONS_1)
        self.assertEqual(a.dates(), DATES_1)
        self.assertEqual(len(b), len(DATES_2))
        self.assertEqual(b.persons(), PERSONS_2)
        self.assertEqual(b.dates(), DATES_2)

    def test_add_person(self):
        r = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_2))
        row = ('aaa', 'Mr A', 0, '')
        r.add_person(*row)
        a = r.persons()
        b = PERSONS_3 + [row]
        self.assertEqual(r.persons(), PERSONS_3 + [row])

    def test_remove_existing_person(self):
        r = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_1))
        person = PERSONS_3[-1][0]
        r.remove_person(person)
        self.assertEqual(r.persons(), PERSONS_2)

    def test_remove_missing_person(self):
        r = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_1))
        person = 'this is a missing name'
        r.remove_person(person)
        self.assertEqual(r.persons(), PERSONS_3)

    def test_roll(self):
        r = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_1))
        N = 10
        r.roll(N)
        self.assertEqual(len(r), len(DATES_1) + N + 1)

    def test_stats(self):
        r = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_1))
        r.roll(10)
        print(r._dates_table())
        print()
        print(r.stats())
        print()
        print(r.stats('20171128'))


class TestRota_Assign(unittest.TestCase):
    def test_assign_from_empty(self):
        r = Rota()
        r.add_person('xxx', 'Mr X', 0, '')
        r.add_person('yyy', 'Mr Y', 0, '')
        r.add_person('zzz', 'Mr Z', 0, '')
        N = 10
        for _ in range(N):
            r.assign()
        self.assertEqual(len(r), N)
        dd = r.dates()
        self.assertEqual(dd[0][2], 'xxx')
        self.assertEqual(dd[1][2], 'yyy')
        self.assertEqual(dd[2][2], 'zzz')


    def test_assign_with_wfh(self):
        r = Rota()
        r.add_person('xxx', 'Mr X', 0, 'Mon')
        r.add_person('yyy', 'Mr Y', 0, 'Tue Wed')
        r.add_person('zzz', 'Mr Z', 0, '')
        N = 10
        for _ in range(N):
            r.assign()
        r.add_person('aaa', 'Mr A', 0, '')
        r.save(None)
        self.assertEqual(len(r), N)
        self.assertFalse(any(oncall == 'xxx' and dow in 'Mon'  for date, dow, oncall, unavail, hols in r.dates()))
        self.assertFalse(any(oncall == 'yyy' and dow in 'Tue Wed'  for date, dow, oncall, unavail, hols in r.dates()))


class TestRota_LoadAndSave(unittest.TestCase):
    def test_load_none(self):
        r = Rota().load(None)
        self.assertEqual(len(r), 0)
        self.assertEqual(len(r.persons()), 0)
        self.assertEqual(len(r.dates()), 0)

    def test_load_empty(self):
        r = Rota().load(StringIO(''))
        self.assertEqual(len(r), 0)
        self.assertEqual(len(r.persons()), 0)
        self.assertEqual(len(r.dates()), 0)

    def test_load_no_data(self):
        r = Rota().load(make_input_file(persons=[], dates=[]))
        self.assertEqual(len(r), 0)
        self.assertEqual(len(r.persons()), 0)
        self.assertEqual(len(r.dates()), 0)

    def test_load_some_data(self):
        r = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_3))
        self.assertEqual(len(r), len(DATES_3))
        self.assertEqual(len(r.persons()), len(PERSONS_3))
        self.assertEqual(len(r.dates()), len(DATES_3))
        self.assertTrue(PERSONS_3[0] in r.persons())
        self.assertTrue(PERSONS_3[1] in r.persons())
        self.assertTrue(PERSONS_3[2] in r.persons())

    def test_load_again(self):
        r = Rota()
        self.assertEqual(len(r), 0)

        r = Rota().load(make_input_file(persons=[], dates=DATES_1))
        self.assertEqual(len(r), len(DATES_1))

        r = Rota().load(make_input_file(persons=[], dates=DATES_3))
        self.assertEqual(len(r), len(DATES_3))

        r = Rota().load(make_input_file(persons=[], dates=DATES_2))
        self.assertEqual(len(r), len(DATES_2))

    # def test_save_none(self):
    #     r = Rota().save(None)
    #     r = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_3)).save(None)

    def test_save_file(self):
        with CliRunner().isolated_filesystem():
            path = 'test_support1.txt'
            r = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_3)).save(path)
            self.assertTrue(os.path.exists(path))
            self.assertEqual(file_line_count(path), 1 + len(PERSONS_3) + 1 + len(DATES_3))
            self.assertTrue(file_contains(path, 'Comment line 1'), 0)
            self.assertTrue(file_contains(path, 'Comment line 2'), 0)
            self.assertTrue(file_contains(path, 'PERSON'), 0)
            self.assertTrue(file_contains(path, 'DATE'), 0)
            self.assertFalse(file_contains(path, 'not defined'), 0)

    def test_save_load(self):
        with CliRunner().isolated_filesystem():
            path = 'test_support2.txt'
            saved = Rota().load(make_input_file(persons=PERSONS_3, dates=DATES_3)).save(path)
            loaded = Rota().load(path)
            self.assertTrue(os.path.exists(path))
            self.assertEqual(len(loaded), len(saved))
            self.assertEqual(loaded.persons(), saved.persons())
            self.assertEqual(loaded.dates(), saved.dates())
            self.assertEqual(loaded.persons(), PERSONS_3)
            self.assertEqual(loaded.dates(), DATES_3)

# class TestCLI(unittest.TestCase):
#     def test_print_sample_file(self):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['print-sample-file'])
#         self.assertEqual(result.exit_code, 0)
#         self.assertIn('#', result.output)
#         self.assertIn('PERSON', result.output)
#         self.assertIn('DATE', result.output)
#
#     def test_print_joiner_instructions(self):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['print-joiner-instructions'])
#         self.assertEqual(result.exit_code, 0)
#
#     def test_print_leaver_instructions(self):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['print-leaver-instructions'])
#         self.assertTrue(result.exit_code == 0)
#
#     def test_assign(self):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['assign'])
#         self.assertEqual(result.exit_code, 0)
#
#     def test_show(self):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['show'])
#         self.assertEqual(result.exit_code, 0)
#
#     def test_status(self):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['status'])
#         self.assertEqual(result.exit_code, 0)
#
#     def test_summary(self):
#         runner = CliRunner()
#         result = runner.invoke(cli, ['summary'])
#         self.assertEqual(result.exit_code, 0)
