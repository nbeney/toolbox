from __future__ import print_function

import csv
import datetime
import itertools
import os
import sys
from collections import namedtuple

from pyDatalog import Logic
from pyDatalog import pyDatalog as pdl

from cbclick import group, option, argument, pass_context, pass_obj

# For convenience only so that we can type pdl.Term later.
pdl.Term = pdl.pyParser.Term

#
# Constants
#

DUMMY_PERSON = None
DUMMY_NAME = None
DUMMY_DATE = '19700101'

SAMPLE_FILE = '''
#  ...
#  ...
#  ...


PERSON  |  NAME             |  INITIAL_SCORE  |  RECURRING_WFH_DAYS
--------+-------------------+-----------------+--------------------
alice   |  Alice Anderson   |  0              |
benno   |  Benno Brown      |  1              |  Fri
chloe   |  Chloe Church     |  1.4            |
david   |  David Davidson   |  0              |  Tue Thu
ellen   |  Ellen Eleanor    |  0              |


DATE     | DOW | ONCALL   | UNAVAILABLE | HOLIDAYS
---------+-----+----------+-------------+---------
'''[1:]


#
# Utilities
#

def for_pdl(func):
    setattr(for_pdl, 'registered_funcs', getattr(for_pdl, 'registered_funcs', []) + [func.__name__])
    return func


def display(res, file=None):
    print(res, file=file)
    print(file=file)


def dump_facts():
    m = Logic(True)
    for v in sorted(m.Db.values(), key=str):
        if v.name[0] in 'abcdefghijklmnopqrstuvwxyz' and '==' not in v.name:
            for c in v.db.values():
                if not c.body:
                    print('+', c.head)


def dump_all():
    m = Logic(True)
    for v in sorted(m.Db.values(), key=str):
        for c in v.db.values():
            if not c.body:
                print('+', c.head)
            else:
                print(c.head, '<=', c.body)


@for_pdl
def join(items):
    return ' '.join(items)


@for_pdl
def today():
    return datetime.datetime.today().strftime('%Y%m%d')


@for_pdl
def get_dow(date):
    dd = datetime.datetime.strptime(date, '%Y%m%d')
    return dd.strftime('%a')


@for_pdl
def get_unavailable_list(date, rota):
    Person, = vars(1)
    return ' '.join([_[0] for _ in sorted(rota.is_unavailable(date, Person).data)])


@for_pdl
def get_onhols_list(date, rota):
    Person, = vars(1)
    return ' '.join([_[0] for _ in sorted(rota.is_onhols(date, Person).data)])


@for_pdl
def next_weekday(date, n=1):
    dd = datetime.datetime.strptime(date, '%Y%m%d')
    dd += datetime.timedelta(days=n)
    if dd.isoweekday() in (6, 7):
        dd += datetime.timedelta(days=8 - dd.isoweekday())
    return dd.strftime('%Y%m%d')


@for_pdl
def prev_weekday(date, n=1):
    dd = datetime.datetime.strptime(date, '%Y%m%d')
    dd += datetime.timedelta(days=-n)
    if dd.isoweekday() in (6, 7):
        dd += datetime.timedelta(days=5 - dd.isoweekday())
    return dd.strftime('%Y%m%d')


def curr_weekday():
    now = datetime.datetime.now()
    if now.isoweekday() > 5:
        now -= datetime.timedelta(days=now.isoweekday() - 5)
    return now.strftime('%Y%m%d')


def date_range(from_date, to_date):
    curr_date = from_date
    while True:
        yield curr_date
        curr_date = next_weekday(curr_date)
        if curr_date > to_date:
            break


#
# Rota class
#

var_id = itertools.count()


def vars(count):
    return [pdl.Variable('X{}'.format(next(var_id))) for _ in range(count)]


class Table:
    def __init__(self, query, vars, order_by=[], headers=[]):
        self.query = query
        self.vars = vars
        self.order_by = order_by or vars
        self.headers = headers or [_._pyD_name for _ in vars]

    def __repr__(self):
        rows = self.data()
        return Table.format(self.headers, rows)

    def data(self):
        safe = Table.safe_value
        nrows = len(self.vars[0].data)
        rows1 = sorted(tuple(safe(var.data[row]) for var in self.order_by + self.vars) for row in range(nrows))
        rows2 = [_[len(self.order_by):] for _ in rows1]
        return rows2

    @classmethod
    def format(cls, headers, rows):
        safe = Table.safe_value
        ncols = len(headers)
        widths_h = [len(header) for header in headers]
        widths_r = [max(len(str(safe(row[col]))) for row in rows) for col in range(ncols)] if rows else [0] * ncols
        widths = [max(widths_h[col], widths_r[col]) for col in range(ncols)]
        formats = ['%-{}s'.format(_) for _ in widths]
        header_lines = ['  |  '.join(formats[col] % headers[col] for col in range(ncols))]
        sep_lines = ['--+--'.join('-' * _ for _ in widths)]
        data_lines = ['  |  '.join(formats[col] % str(safe(row[col])) for col in range(ncols)) for row in rows]
        return '\n'.join(header_lines + sep_lines + data_lines)

    @classmethod
    def safe_value(cls, value):
        return '' if value is None else value


class Rota:
    last_instance = None

    def _new_instance(self):
        if Rota.last_instance is not None:
            Rota.last_instance._logic = Logic(True)
        Logic()
        Rota.last_instance = self

    def _check_instance(self):
        if id(self) != id(Rota.last_instance):
            Rota.last_instance._logic = Logic(True)
            Rota.last_instance = self
            Logic(self._logic)

    def __init__(self):
        self._new_instance()
        self.file_header_lines = None
        self._reinit_pdl(None)

    def load(self, path_or_file):
        self._check_instance()
        if isinstance(path_or_file, str):
            path = path_or_file
            with open(path, 'r') as f:
                self._reinit_pdl(f)
        else:
            f = path_or_file
            self._reinit_pdl(f)
        return self

    def save(self, path_or_file):
        self._check_instance()
        if isinstance(path_or_file, str):
            path = path_or_file
            with open(path, 'w') as f:
                self._write_facts_to_file(f)
        else:
            f = path_or_file
            self._write_facts_to_file(f)
        return self

    def __len__(self):
        self._check_instance()
        Date, Person = vars(2)
        res = self.is_oncall_filt(Date, Person)
        return len(res.data)

    def persons(self):
        self._check_instance()
        return self._persons_table().data()

    def dates(self):
        self._check_instance()
        return self._dates_table().data()

    def add_person(self, person, name, initial, wfh_str):
        self._check_instance()
        A, B, C, D, E = vars(5)
        rank = len(self.person_filt(A, B, C, D, E)) + 1
        + self.person_raw(rank, person, name, initial, wfh_str.split(' '))
        return self

    def remove_person(self, person):
        self._check_instance()
        Rank, Name, Initial, WfhList = vars(4)
        res = self.person_raw(Rank, person, Name, Initial, WfhList)
        if res:
            - self.person_raw(Rank.v(), person, Name.v(), Initial.v(), WfhList.v())
        return self

    def set_initial(self, person, initial):
        self._check_instance()
        Rank, Name, Initial, WfhList = vars(4)
        res = self.person_raw(Rank, person, Name, Initial, WfhList)
        if res:
            - self.person_raw(Rank.v(), person, Name.v(), Initial.v(), WfhList.v())
            + self.person_raw(Rank.v(), person, Name.v(), initial, WfhList.v())
        return self

    def set_wfh_list(self, person, wfh_list):
        self._check_instance()
        Rank, Name, Initial, WfhList = vars(4)
        res = self.person_raw(Rank, person, Name, Initial, WfhList)
        if res:
            - self.person_raw(Rank.v(), person, Name.v(), Initial.v(), WfhList.v())
            + self.person_raw(Rank.v(), person, Name.v(), Initial.v(), wfh_list)
        return self

    def set_oncall(self, person, date, flag):
        self._check_instance()
        if flag:
            + self.is_oncall_raw(date, person)
        else:
            - self.is_oncall_raw(date, person)
        return self

    def set_unavailable(self, person, date, flag):
        self._check_instance()
        if flag:
            + self.is_unavailable(date, person)
            if ~self.oncall_date(date):
                + self.is_oncall_raw(date, None)
        else:
            - self.is_unavailable(date, person)
        return self

    def set_holidays(self, person, date, flag):
        self._check_instance()
        if flag:
            + self.is_onhols(date, person)
            if ~self.oncall_date(date):
                + self.is_oncall_raw(date, None)
        else:
            - self.is_onhols(date, person)
        return self

    def assign(self):
        self._check_instance()
        LastDate, NextDate, Any, Person = vars(4)

        date_qry = (LastDate == self.last_oncall_date[None]) & (NextDate == self.next_oncall_date[LastDate])

        res = date_qry & (Person == self.next_oncall_person[NextDate])
        if res:
            last_date, next_date, next_person = res.v()
            + self.is_oncall_raw(next_date, next_person)
        else:
            res = date_qry
            if res:
                last_date, next_date = res.v()
                print('ERROR: Could not find a solution for {}!'.format(next_date))
                print()
                display(stats(last_date))
                display(stats(next_date))
                sys.exit(1)
            else:
                next_date = today()
                res = (Person == self.next_oncall_person[next_date])
                next_person = res[0][0]
                + self.is_oncall_raw(next_date, next_person)

        return self

    def assign_until(self, to_date):
        pass

    def roll(self, ndays):
        self._check_instance()
        dd = today()
        for _ in range(ndays + 1):
            if ~self.oncall_date(dd):
                + self.is_oncall_raw(dd, None)
            dd = next_weekday(dd)

        return self

    def stats(self, date=None):
        self._check_instance()
        Date, Dow, Rank, Person, Name, Score, Initial, Oncall, Unavailable, Holidays, Status, WfhList = vars(12)

        date_cond = (Date == date) if date else (Date == self.last_oncall_date[None])

        return Table(
            query=(
                self.person_filt(Rank, Person, Name, Initial, WfhList) &
                date_cond &
                (Dow == get_dow(Date)) &
                (Score == self.score[Date, Person]) &
                (Oncall == self.count_oncall[Date, Person]) &
                (Unavailable == self.count_unavailable[Date, Person]) &
                (Holidays == self.count_onhols[Date, Person]) &
                (Status == self.status[Date, Person])
            ),
            vars=[Person, Score, Initial, Oncall, Unavailable, Holidays, Status, Date, Dow],
            order_by=[Person],
            headers=['PERSON', 'SCORE', 'INITIAL', 'ONCALL', 'UNAVAILABLE', 'HOLIDAYS', 'STATUS', 'DATE', 'DOW'],
        )

    def schedule(self, from_date=None, to_date=None, no_status=False, no_score=False):
        if from_date is None and to_date is None:
            from_date = today()

        Date, Dow, Rank, Person, Name, Initial, WfhList = vars(7)
        query = self.oncall_date(Date) & (Dow == get_dow(Date)) & self.is_oncall_raw(Date, Person)

        if from_date:
            query &= (Date >= from_date)
        if to_date:
            query &= (Date <= to_date)

        person = pdl.Term('person')
        person(Person) <= self.person_filt(Rank, Person, Name, Initial, WfhList)

        vars_ = [Date, Dow, Person]
        headers = ['DATE', 'DOW', 'ONCALL']

        status_vars = {pp: pdl.Variable('STATUS-' + pp) for (pp,) in person(Person).data}
        score_vars = {pp: pdl.Variable('SCORE-' + pp) for (pp,) in person(Person).data}
        for (pp,) in sorted(person(Person).data):
            if not no_status:
                query &= (status_vars[pp] == self.status[Date, pp])
                vars_.append(status_vars[pp])
                headers.append(status_vars[pp]._pyD_name)
            if not no_score:
                query &= (score_vars[pp] == self.score[Date, pp])
                vars_.append(score_vars[pp])
                headers.append(score_vars[pp]._pyD_name)

        return Table(
            query=query,
            vars=vars_,
            headers=headers,
        )

    def _persons_table(self):
        Rank, Person, Name, Score, WfhList, WfhStr = vars(6)
        res = Table(
            query=self.person_filt(Rank, Person, Name, Score, WfhList) & (WfhStr == join(WfhList)),
            vars=[Person, Name, Score, WfhStr],
            order_by=[Rank, Person],
            headers=['PERSON', 'NAME', 'INITIAL', 'RECURRING_WFH_DAYS'],
        )
        return res

    def _dates_table(self):
        Date, Dow, Person, Unavailable, Holidays = vars(5)
        res = Table(
            query=(
                self.is_oncall_filt(Date, Person) &
                (Dow == get_dow(Date)) &
                (Unavailable == get_unavailable_list(Date, self)) &
                (Holidays == get_onhols_list(Date, self))
            ),
            vars=[Date, Dow, Person, Unavailable, Holidays],
            headers=['DATE', 'DOW', 'ONCALL', 'UNAVAILABLE', 'HOLIDAYS'],
        )
        return res

    def _reinit_pdl_facts(self):
        self.person_raw = pdl.Term('person_raw')
        + self.person_raw(0, DUMMY_PERSON, DUMMY_NAME, 0, '')

        self.is_oncall_raw = pdl.Term('is_oncall_raw')
        + self.is_oncall_raw(DUMMY_DATE, None)

        self.is_onhols = pdl.Term('is_onhols')
        + self.is_onhols(DUMMY_DATE, None)

        self.is_unavailable = pdl.Term('is_unavailable')
        + self.is_unavailable(DUMMY_DATE, None)

    def _reinit_pdl_predicates(self):
        Rank, Person, Name, Initial, WfhList = vars(5)
        self.person_filt = pdl.Term('person_filt')
        self.person_filt(Rank, Person, Name, Initial, WfhList) <= (
            self.person_raw(Rank, Person, Name, Initial, WfhList) & (Person != DUMMY_PERSON))

        Date, Person = vars(2)
        self.is_oncall_filt = pdl.Term('is_oncall_filt')
        self.is_oncall_filt(Date, Person) <= self.is_oncall_raw(Date, Person) & (Date != DUMMY_DATE)

        Date, X = vars(2)
        self.oncall_date = pdl.Term('oncall_date')
        self.oncall_date(Date) <= (
            self.is_oncall_filt(Date, Person) &
            self.person_filt(Rank, Person, Name, Initial, WfhList)
        )

        PrevDate, = vars(1)
        self.is_back_from_hols = pdl.Term('is_back_from_hols')
        self.is_back_from_hols(Date, Person) <= (
            ~self.is_onhols(Date, Person) &
            (PrevDate == prev_weekday(Date)) &
            self.is_onhols(PrevDate, Person)
        )

        self.is_wfh = pdl.Term('is_wfh')
        self.is_wfh(Date, Person) <= self.person_filt(Rank, Person, Name, Initial, WfhList) & get_dow(Date).in_(WfhList)

    def _reinit_pdl_functions(self):
        Person, Date, X, Y, Z, A, Initial, Score, Rank = vars(9)

        self.status = pdl.Term('status')
        self.status[Date, Person] = '-'
        (self.status[Date, Person] == 'At home') <= (self.is_wfh(Date, Person))
        (self.status[Date, Person] == 'On hols') <= (self.is_onhols(Date, Person))
        (self.status[Date, Person] == 'Unavailable') <= (self.is_unavailable(Date, Person))
        (self.status[Date, Person] == 'Back from hols') <= (self.is_back_from_hols(Date, Person))
        (self.status[Date, Person] == 'Oncall') <= (self.is_oncall_filt(Date, Person))

        self.last_oncall_date = pdl.Term('last_oncall_date')
        (self.last_oncall_date[None] == _max(X, order_by=X)) <= self.oncall_date(X)
        (self.last_oncall_date[None] == today()) <= ~self.oncall_date(X)

        self.next_oncall_date = pdl.Term('next_oncall_date')
        self.next_oncall_date[Date] = next_weekday(Date)
        self.next_oncall_date[None] = next_weekday(self.last_oncall_date[None])

        self.count_oncall = pdl.Term('count_oncall')
        self.count_oncall[Date, Person] = 0
        (self.count_oncall[Date, Person] == _len(X)) <= self.is_oncall_filt(X, Person) & (X <= Date)

        self.count_onhols = pdl.Term('count_onhols')
        self.count_onhols[Date, Person] = 0
        (self.count_onhols[Date, Person] == _len(X)) <= self.is_onhols(X, Person) & (X <= Date)

        self.count_unavailable = pdl.Term('count_unavailable')
        self.count_unavailable[Date, Person] = 0
        (self.count_unavailable[Date, Person] == _len(X)) <= self.is_unavailable(X, Person) & (X <= Date)

        self.count_persons = pdl.Term('count_persons')
        (self.count_persons[None] == _len(Person)) <= self.person_filt(A, Person, X, Y, Z)

        initial = pdl.Term('initial')
        (initial[Person] == Initial) <= self.person_filt(Z, Person, X, Initial, Y)
        self.score = pdl.Term('score')
        self.score[Date, Person] = (
            initial[Person] + self.count_oncall[Date, Person] + 1.0 * self.count_onhols[Date, Person] /
            self.count_persons[None])

        rank = pdl.Term('rank')
        (rank[Person] == Rank) <= self.person_filt(Rank, Person, X, Y, Z)
        self.ranked_score = pdl.Term('ranked_score')
        self.ranked_score[Date, Person] = 10000 * self.score[Date, Person] + rank[Person]

        self.next_oncall_person = pdl.Term('next_oncall_person')
        (self.next_oncall_person[Date] == _min(Person, order_by=Score)) <= (
            self.person_filt(A, Person, X, Y, Z) &
            ~self.is_onhols(Date, Person) &
            ~self.is_unavailable(Date, Person) &
            ~self.is_back_from_hols(Date, Person) &
            ~self.is_wfh(Date, Person) &
            (Score == self.ranked_score[Date, Person]))

    def _reinit_pdl(self, f):
        pdl.clear()
        self._reinit_pdl_facts()
        self._reinit_pdl_predicates()
        self._reinit_pdl_functions()
        if f:
            self._read_facts_from_file(f)

    def _read_facts_from_file(self, f):
        self.file_header_lines = []

        in_person_section = False
        in_date_section = False
        rank = 0

        for row in csv.reader(f, delimiter='|'):
            # Strip the leading and trailing spaces in each value.
            row = [_.strip() for _ in row]

            # Skip the empty lines.
            if len(row) == 0 or row[0] == '':
                continue

            # Collect all the comment lines so that they are preserved when the file is regenerated.
            if row[0].startswith('#'):
                self.file_header_lines.append(','.join(row))
                continue

            # Are we starting the PERSON or DATE section?
            if row[0] == 'PERSON':
                in_person_section = True
                continue
            if row[0] == 'DATE':
                in_person_section = False
                in_date_section = True
                continue

            # Process the line according to the current section.
            if (in_person_section or in_date_section) and row[0].startswith('--'):
                continue
            elif in_person_section and len(row) >= 4:
                person_, name_, initial_score_, wfh_days_ = row[:4]
                rank += 1
                + self.person_raw(rank, person_, name_, float(initial_score_), wfh_days_.split(' '))
            elif in_date_section and len(row) >= 5:
                date_, dow_, oncall_, unavailable_, onhols_ = row[:5]
                if oncall_:
                    + self.is_oncall_raw(date_, oncall_)
                if unavailable_:
                    for p in unavailable_.split(' '):
                        + self.is_unavailable(date_, p)
                if onhols_:
                    for p in onhols_.split(' '):
                        + self.is_onhols(date_, p)

    def _write_facts_to_file(self, f):
        if self.file_header_lines:
            print('\n'.join(self.file_header_lines), file=f)
            print(file=f)
            print(file=f)

        display(self._persons_table(), file=f)
        print(file=f)

        display(self._dates_table(), file=f)


#
# Command line interface
#

Common = namedtuple('Common', ['file'])


@group(context_settings=dict(terminal_width=200, help_option_names=['-h', '--help']), help='Manage our support rota.')
@option('-f', '--file', default='./support.txt', show_default=True,
        help='The CSV file used to keep track of assignments, holidays, etc.')
@pass_context
def cli(ctx, file):
    ctx.obj = Common(file=file)


@cli.command(help='Print the full help.')
@pass_context
def help(ctx):
    separator = '\n' + '-' * 79 + '\n'
    print(ctx.parent.get_help())
    for name, cmd in sorted(ctx.parent.command.commands.items()):
        print(separator)
        print(cmd.get_help(ctx).replace('support.py help', 'support.py ' + name))


@cli.command(help='Add a person to the rota.')
@argument('person')
@argument('name')
@argument('initial', type=float)
@argument('wfh_str')
@pass_obj
def add_person(obj, person, name, initial, wfh_str):
    r = Rota().load(obj.file) if os.path.exists(obj.file) else Rota()
    r.add_person(person, name, initial, wfh_str).save(obj.file)


@cli.command(help='Remove a person from the rota.')
@argument('person')
@pass_obj
def remove_person(obj, person):
    Rota().load(obj.file).remove_person(person).save(obj.file)


@cli.command(help='Set the initial score for a person.')
@argument('person')
@argument('initial', type=float)
@pass_obj
def set_initial(obj, person, initial):
    Rota().load(obj.file).set_initial(person, initial).save(obj.file)


@cli.command(help='Set the WFH days for a person.')
@argument('person')
@argument('wfh_str')
@pass_obj
def set_wfh_days(obj, person, wfh_str):
    Rota().load(obj.file).set_wfh_list(person, wfh_str.split(' ')).save(obj.file)


@cli.command(help='Set the oncall status for a person on a date.')
@argument('person')
@argument('date')
@argument('flag', type=bool)
@pass_obj
def set_oncall(obj, date, person, flag):
    Rota().load(obj.file).set_oncall(person, date, flag).save(obj.file)


@cli.command(help='Set the unavailable status for a person on a date.')
@argument('person')
@argument('date')
@argument('flag', type=bool)
@pass_obj
def set_unavailable(obj, date, person, flag):
    Rota().load(obj.file).set_unavailable(person, date, flag).save(obj.file)


@cli.command(help='Set the holidays status for a person on a date.')
@argument('person')
@argument('date')
@argument('flag', type=bool)
@pass_obj
def set_holidays(obj, date, person, flag):
    Rota().load(obj.file).set_holidays(person, date, flag).save(obj.file)


@cli.command(help='Assign the next oncall person.')
@pass_obj
def assign(obj):
    Rota().load(obj.file).assign().save(obj.file)


@cli.command(help='Show who is oncall.')
@option('-f', '--from-date', default=curr_weekday(), show_default=True,
        help='The absolute start date (YYYYMMDD).')
@option('-t', '--to-date', default=curr_weekday(), show_default=True, help='The absolute end date (YYYYMMDD).')
@option('-F', '--from-days', type=int,
        help='The relative start date expressed in number of days before the current date (takes precedence over --from-date).')
@option('-T', '--to-days', type=int,
        help='The relative end date expressed in number of days after the current date (takes precedence over --to-date).')
@pass_obj
def show(obj, from_date, to_date, from_days, to_days):
    if from_days is not None:
        from_date = prev_weekday(curr_weekday(), n=from_days)
    if to_days is not None:
        to_date = next_weekday(curr_weekday(), n=to_days)
    r = Rota().load(obj.file)
    r.assign_until(to_date)
    # for date in date_range(from_date, to_date):
    #     res = is_oncall_filt(date, Person).v()
    #     print('{} : {}'.format(date, res[0] if res else '???'))


@cli.command(help='Show the status for each person.')
@option('-f', '--from-date', default=curr_weekday(), show_default=True,
        help='The absolute start date (YYYYMMDD).')
@option('-t', '--to-date', default=curr_weekday(), show_default=True, help='The absolute end date (YYYYMMDD).')
@option('-F', '--from-days', type=int,
        help='The relative start date expressed in number of days before the current date (takes precedence over --from-date).')
@option('-T', '--to-days', type=int,
        help='The relative end date expressed in number of days after the current date (takes precedence over --to-date).')
@pass_obj
def status(obj, from_date, to_date, from_days, to_days):
    if from_days is not None:
        from_date = prev_weekday(curr_weekday(), n=from_days)
    if to_days is not None:
        to_date = next_weekday(curr_weekday(), n=to_days)
    r = Rota().load(obj.file)
    r.assign_until(to_date)
    # for date in date_range(from_date, to_date):
    #     display(stats(date))


@cli.command(help='Show the summary.')
@option('-f', '--from-date', default=curr_weekday(), show_default=True,
        help='The absolute start date (YYYYMMDD).')
@option('-t', '--to-date', default=next_weekday(curr_weekday(), n=7), show_default=True,
        help='The absolute end date (YYYYMMDD).')
@option('-F', '--from-days', type=int,
        help='The relative start date expressed in number of days before the current date (takes precedence over --from-date).')
@option('-T', '--to-days', type=int,
        help='The relative end date expressed in number of days after the current date (takes precedence over --to-date).')
@option('--no-status', type=bool, is_flag=True, help='Discard the STATUS columns.')
@option('--no-score', type=bool, is_flag=True, help='Discard the SCORE columns.')
@pass_obj
def summary(obj, from_date, to_date, from_days, to_days, no_status, no_score):
    if from_days is not None:
        from_date = prev_weekday(curr_weekday(), n=from_days)
    if to_days is not None:
        to_date = next_weekday(curr_weekday(), n=to_days)
    r = Rota().load(obj.file)
    r.assign_until(to_date)
    # display(schedule(from_date, to_date, no_status, no_score))


@cli.command(help='Print the a sample file to help you getting started.')
@pass_obj
def sample_file(obj):
    print(SAMPLE_FILE)


#
# Main
#

# To define the aggregate functions (eg len_, min_) and link PDL to the functions that are decorated with @for_pdl.
pdl.create_terms(*for_pdl.registered_funcs)

if __name__ == '__main__':
    cli()
