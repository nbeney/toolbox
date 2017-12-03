# TODO: Add empty dates to file
# TODO: Schedule for next days
# TODO: Add unit tests
# TODO: Change file format
# TODO: Move person, name, initial, wfh_days to file
# TODO: Calculate holiday ratio on the fly

# This script must be updated when people join or leave the CBTech team. Search for the 'MAINTENANCE' string in this
# file to find out where changes are required.

from __future__ import print_function

import csv
import datetime
import sys

from pyDatalog import Logic
from pyDatalog import pyDatalog as pdl

from cbclick import group, option, pass_context, pass_obj

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


PERSON  | NAME             | INITIAL_SCORE | RECURRING_WFH_DAYS
--------|------------------|---------------|-------------------
alice   | Alice Anderson   | 0             |
benno   | Benno Brown      | 1             | Fri
chloe   | Chloe Church     | 1.4           |
david   | David Davidson   | 0             | Tue Thu
ellen   | Ellen Eleanor    | 0             |


DATE     | DOW | ONCALL   | UNAVAILABLE | HOLIDAYS
---------|-----|----------|-------------|---------
'''[1:]


#
# Utilities
#

def for_pdl(func):
    setattr(for_pdl, 'registered_funcs', getattr(for_pdl, 'registered_funcs', []) + [func.__name__])
    return func


def display(res, file=None):
    print(res.sort(), file=file)
    print(file=file)


# def stats(date=None):
#     Initial = pdl.Variable('INITIAL')
#     Oncall = pdl.Variable('ONCALL')
#     Unavailable = pdl.Variable('UNAVAILABLE')
#     Onhols = pdl.Variable('HOLIDAYS')
#     Status = pdl.Variable('STATUS')
#
#     date_cond = (Date == date) if date else last_oncall_date(Date)
#
#     return (person(Person)) & \
#            date_cond & \
#            (Dow == get_dow(Date)) & \
#            (Score == score[Date, Person]) & \
#            initial_score(Person, Initial) & \
#            (Oncall == count_oncall[Date, Person]) & \
#            (Unavailable == count_unavailable[Date, Person]) & \
#            (Onhols == count_onhols[Date, Person]) & \
#            (Status == status[Date, Person])
#
#
# def schedule(from_date=None, to_date=None, no_status=False, no_score=False):
#     query = oncall_date(Date) & (Dow == get_dow(Date)) & is_oncall_raw(Date, Person)
#
#     if from_date:
#         query &= (Date >= from_date)
#     if to_date:
#         query &= (Date <= to_date)
#
#     status_vars = {pp: pdl.Variable('STATUS-' + pp) for (pp,) in person(Person).data}
#     score_vars = {pp: pdl.Variable('SCORE-' + pp) for (pp,) in person(Person).data}
#     for (pp,) in sorted(person(Person).data):
#         if not no_status:
#             query &= (status_vars[pp] == status[Date, pp])
#         if not no_score:
#             query &= (score_vars[pp] == score[Date, pp])
#
#     return query


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
def today():
    return datetime.datetime.today().strftime('%Y%m%d')


@for_pdl
def get_dow(date):
    dd = datetime.datetime.strptime(date, '%Y%m%d')
    return dd.strftime('%a')


@for_pdl
def get_unavailable_list(date, rota):
    Person, = make_vars('Person')
    return ' '.join([_[0] for _ in sorted(rota.is_unavailable(date, Person).data)])


@for_pdl
def get_onhols_list(date, rota):
    Person, = make_vars('Person')
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
# Logic
#

# def reinit_pdl_predicates2():
#     pass
#     global oncall_date
#     oncall_date = pdl.Term('oncall_date')
#     oncall_date(Date) <= (is_oncall_raw(Date, X) & (Date != DUMMY_DATE))
#
#     # global is_back_from_hols
#     # PrevDate = pdl.Variable('PrevDate')
#     # is_back_from_hols = pdl.Term('is_back_from_hols')
#     # is_back_from_hols(Date, Person) <= (
#     #     ~is_onhols(Date, Person) &
#     #     (PrevDate == prev_weekday(Date)) &
#     #     is_onhols(PrevDate, Person)
#     # )
#
#     # global is_at_home
#     # is_at_home = pdl.Term('is_at_home')
#     # + is_at_home(None, None)
#     # # TODO: Use wfh_day instead
#     # is_at_home(Date, Person) <= ((Person == 'orbang') & (get_dow(Date).in_(['Fri'])))
#     # is_at_home(Date, Person) <= ((Person == 'nespor') & (get_dow(Date).in_(['Tue', 'Thu'])))
#
#     # global last_oncall_date
#     # last_oncall_date = pdl.Term('last_oncall_date')
#     # (last_oncall_date[Person] == _max(Date, order_by=Date)) <= (is_oncall_raw(Date, Person) & (Date > DUMMY_DATE))
#     # (last_oncall_date[None] == _max(Date, order_by=Date)) <= (is_oncall_raw(Date, X) & (Date > DUMMY_DATE))
#     # last_oncall_date(Date) <= is_oncall_raw(Date, Person) & (Date > DUMMY_DATE)
#
#     # global next_oncall_date
#     # next_oncall_date = pdl.Term('next_oncall_date')
#     # next_oncall_date[Date] = (next_weekday(Date))
#     # next_oncall_date[None] = (next_weekday(last_oncall_date[None]))
#
#
# def reinit_pdl_functions2():
#     # The order in which the different possible cases for one function is defined matters. PDL search for an applicable
#     # definition from the last definition to the first. So catch all definitions, etc should be defined first.
#
#     # global status
#     # status = pdl.Term('status')
#     # status[Date, Person] = '-'
#     # (status[Date, Person] == 'At home') <= (is_at_home(Date, Person))
#     # (status[Date, Person] == 'On hols') <= (is_onhols(Date, Person))
#     # (status[Date, Person] == 'Unavailable') <= (is_unavailable(Date, Person))
#     # (status[Date, Person] == 'Back from hols') <= (is_back_from_hols(Date, Person))
#     # (status[Date, Person] == 'Oncall') <= (is_oncall_raw(Date, Person))
#
#     # global count_oncall
#     # count_oncall = pdl.Term('count_oncall')
#     # count_oncall[Date, Person] = 0
#     # (count_oncall[Date, Person] == _len(X)) <= (is_oncall_raw(X, Person) & (X <= Date))
#
#     # global count_onhols
#     # count_onhols = pdl.Term('count_onhols')
#     # count_onhols[Date, Person] = 0
#     # (count_onhols[Date, Person] == _len(X)) <= (is_onhols(X, Person) & (X <= Date))
#
#     # global count_unavailable
#     # count_unavailable = pdl.Term('count_unavailable')
#     # count_unavailable[Date, Person] = 0
#     # (count_unavailable[Date, Person] == _len(X)) <= (is_unavailable(X, Person) & (X <= Date))
#
#     # global score
#     # score = pdl.Term('score')
#     # tmp = pdl.Term('tmp')
#     # (tmp[Person] == Initial) <= initial_score(Person, Initial)
#     # score[Date, Person] = (tmp[Person] + count_oncall[Date, Person] + 0.2 * count_onhols[Date, Person])
#
#     # global next_oncall_person
#     # next_oncall_person = pdl.Term('next_oncall_person')
#     # (next_oncall_person[Date] == _min(Person, order_by=Score)) <= (
#     #     person(Person) &
#     #     ~is_onhols(Date, Person) &
#     #     ~is_unavailable(Date, Person) &
#     #     ~is_back_from_hols(Date, Person) &
#     #     ~is_at_home(Date, Person) &
#     #     (Score == score[Date, Person]))


def assign_next():
    LastDate = pdl.Variable('Last Date')
    NextDate = pdl.Variable('Next Date')
    Any = pdl.Variable('Any')

    date_qry = (last_oncall_date(LastDate, Any)) & (NextDate == next_oncall_date[LastDate])

    res = date_qry & (Person == next_oncall_person[NextDate])
    if res:
        last_date, next_date, next_person = res.v()
        + is_oncall_raw(next_date, next_person)
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
            res = (Person == next_oncall_person[next_date])
            next_person = res[0][0]
            + is_oncall_raw(next_date, next_person)


def assign_until(date):
    while is_oncall_raw(date, Person).data == []:
        assign_next()


#
# Rota class
#

def make_vars(*names):
    return [pdl.Variable(_) for _ in names]


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
        Date, Person = make_vars('Date', 'Person')
        res = self.is_oncall_filt(Date, Person)
        return len(res.data)

    def persons(self):
        self._check_instance()
        Person, Name, Score, Days, Rank = make_vars('Person', 'Name', 'Score', 'Days', 'Rank')
        res = self.person_filt(Person, Name, Score, Days, Rank)
        return sorted(res.data)

    def dates(self):
        self._check_instance()
        temp = pdl.Term('temp')
        Date, Dow, Person, Unavailable, Holidays = make_vars('Date', 'Dow', 'Person', 'Unavailable', 'Holidays')
        temp(Date, Dow, Person, Unavailable, Holidays) <= (
            self.is_oncall_filt(Date, Person) &
            (Dow == get_dow(Date)) &
            (Unavailable == get_unavailable_list(Date, self)) &
            (Holidays == get_onhols_list(Date, self))
        )
        res = temp(Date, Dow, Person, Unavailable, Holidays)
        return sorted(res.data)

    def add_person(self, person, name, initial, wfh_days, rank):
        self._check_instance()
        + self.person_raw(person, name, initial, wfh_days, rank)

    def remove_person(self, person):
        self._check_instance()
        Name, Initial, WfhDays, Rank = make_vars('Name', 'Initial', 'WfhDays', 'Rank')
        res = self.person_raw(person, Name, Initial, WfhDays, Rank)
        if res:
            - self.person_raw(person, Name.v(), Initial.v(), WfhDays.v(), Rank.v())

    def assign(self):
        self._check_instance()
        LastDate, NextDate, Any, Person = make_vars('LastDate', 'NextDate', 'Any', 'Person')

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

    def _reinit_pdl_facts(self):
        self.person_raw = pdl.Term('person_raw')
        + self.person_raw(DUMMY_PERSON, DUMMY_NAME, 0, '', 0)

        self.is_oncall_raw = pdl.Term('is_oncall_raw')
        + self.is_oncall_raw(DUMMY_DATE, None)

        self.is_onhols = pdl.Term('is_onhols')
        + self.is_onhols(DUMMY_DATE, None)

        self.is_unavailable = pdl.Term('is_unavailable')
        + self.is_unavailable(DUMMY_DATE, None)

        initial_score = pdl.Term('initial_score')
        + initial_score(DUMMY_PERSON, 0)

    def _reinit_pdl_predicates(self):
        Person, Name, Initial, WfhDays, Rank = make_vars('Person', 'Name', 'Initial', 'WfhDays', 'Rank')
        self.person_filt = pdl.Term('person_filt')
        self.person_filt(Person, Name, Initial, WfhDays, Rank) <= (
            self.person_raw(Person, Name, Initial, WfhDays, Rank) & (Person != DUMMY_PERSON))

        Date, Person = make_vars('Date', 'Person')
        self.is_oncall_filt = pdl.Term('is_oncall_filt')
        self.is_oncall_filt(Date, Person) <= self.is_oncall_raw(Date, Person) & (Date != DUMMY_DATE)

        Date, X = make_vars('Date', 'X')
        self.oncall_date = pdl.Term('oncall_date')
        self.oncall_date(Date) <= self.is_oncall_filt(Date, X)

        PrevDate, = make_vars('PrevDate')
        self.is_back_from_hols = pdl.Term('is_back_from_hols')
        self.is_back_from_hols(Date, Person) <= (
            ~self.is_onhols(Date, Person) &
            (PrevDate == prev_weekday(Date)) &
            self.is_onhols(PrevDate, Person)
        )

        self.is_wfh = pdl.Term('is_wfh')
        self.is_wfh(Date, Person) <= self.person_filt(Person, Name, Initial, WfhDays, Rank) & (get_dow(Date) == WfhDays)

    def _reinit_pdl_functions(self):
        Person, Date, X, Y, Z, A, Initial, Score, Rank = make_vars(
            'Person', 'Date', 'X', 'Y', 'Z', 'A', 'Initial', 'Score', 'Rank')

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

        self.score = pdl.Term('score')
        initial = pdl.Term('initial')
        (initial[Person] == Initial) <= self.person_filt(Person, X, Initial, Y, Z)
        rank = pdl.Term('rank')
        (rank[Person] == Rank) <= self.person_filt(Person, X, Y, Z, Rank)
        self.score[Date, Person] = (
            1000 * (initial[Person] + self.count_oncall[Date, Person] + 0.2 * self.count_onhols[Date, Person]) + rank[Person])

        self.next_oncall_person = pdl.Term('next_oncall_person')
        (self.next_oncall_person[Date] == _min(Person, order_by=Score)) <= (
            self.person_filt(Person, X, Y, Z, A) &
            ~self.is_onhols(Date, Person) &
            ~self.is_unavailable(Date, Person) &
            ~self.is_back_from_hols(Date, Person) &
            ~self.is_wfh(Date, Person) &
            (Score == self.score[Date, Person]))

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
                + self.person_raw(person_, name_, float(initial_score_), wfh_days_, rank)
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

        Person, Name, Score, WfhDays, Rank = make_vars('PERSON', 'NAME', 'INITIAL', 'RECURRING_WFH_DAYS', 'Rank')
        temp = pdl.Term('temp')
        temp(Person, Name, Score, WfhDays) <= self.person_filt(Person, Name, Score, WfhDays, Rank)
        display(temp(Person, Name, Score, WfhDays), file=f)
        print(file=f)

        Date, Dow, Oncall, Unavailable, Holidays = make_vars('DATE', 'DOW', 'ONCALL', 'UNAVAILABLE', 'HOLIDAYS')
        display(
            self.oncall_date(Date) &
            (Dow == get_dow(Date)) &
            self.is_oncall_filt(Date, Oncall) &
            (Unavailable == get_unavailable_list(Date, self)) &
            (Holidays == get_onhols_list(Date, self)),
            file=f
        )


#
# Command line interface
#

@group(context_settings=dict(terminal_width=200), help='Manage our support rota.')
@option('-f', '--file', default='./support.txt', show_default=True,
        help='The CSV file used to keep track of assignments, holidays, etc.')
@pass_context
def cli(ctx, file):
    with open(file, 'r') as f:
        reinit_pdl(f)
    ctx.obj = dict(file=file)


@cli.command(help='Assign the next oncall person.')
@pass_obj
def assign(obj):
    display(stats())
    assign_next()
    display(schedule())
    display(stats())
    write_facts_to_file(obj['file'])


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
    # assign_until(to_date)
    for date in date_range(from_date, to_date):
        res = is_oncall_filt(date, Person).v()
        print('{} : {}'.format(date, res[0] if res else '???'))


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
    # assign_until(to_date)
    for date in date_range(from_date, to_date):
        display(stats(date))


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
    # assign_until(to_date)
    display(schedule(from_date, to_date, no_status, no_score))


@cli.command(help='Print the a sample file to help you getting started.')
@pass_obj
def print_sample_file(obj):
    print(SAMPLE_FILE)


@cli.command(help='Print the instructions for a joiner.')
@pass_obj
def print_joiner_instructions(obj):
    # TODO: Implement print_instructions_for_joiner
    pass


@cli.command(help='Print the instructions for a leaver.')
@pass_obj
def print_leaver_instructions(obj):
    # TODO: Implement print_instructions_for_leaver
    pass


#
# Main
#

# To define the aggregate functions (eg len_, min_) and link PDL to the functions that are decorated with @for_pdl.
pdl.create_terms(*for_pdl.registered_funcs)

if __name__ == '__main__':
    cli()
