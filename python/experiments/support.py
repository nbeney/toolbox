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
import unittest

from click.testing import CliRunner
from pyDatalog import Logic
from pyDatalog import pyDatalog as pdl

from cbclick import group, option, pass_context, pass_obj

# For convenience only so that we can type pdl.Term later.
pdl.Term = pdl.pyParser.Term

#
# Constants
#

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
# Globals
#

# Global pyDatalog variables
Date = None
Dow = None
Person = None
Name = None
Initial = None
Score = None
X = None
Y = None
Z = None

# Global pyDatalog facts
person = None
person_name = None
initial_score = None
wfh_day = None
is_oncall = None
is_onhols = None
is_unavailable = None

# Global pyDatalog predicates
oncall_date = None
is_back_from_hols = None
is_at_home = None

# Global pyDatalog functions
status = None
count_oncall = None
count_onhols = None
count_unavailable = None
score = None
last_oncall_date = None
next_oncall_date = None
next_oncall_person = None


#
# Utilities
#

def for_pdl(func):
    setattr(for_pdl, 'registered_funcs', getattr(for_pdl, 'registered_funcs', []) + [func.__name__])
    return func


def display(res, file=None):
    print(res.sort(), file=file)
    print(file=file)


def stats(date=None):
    Initial = pdl.Variable('INITIAL')
    Oncall = pdl.Variable('ONCALL')
    Unavailable = pdl.Variable('UNAVAILABLE')
    Onhols = pdl.Variable('HOLIDAYS')
    Status = pdl.Variable('STATUS')

    date_cond = (Date == date) if date else (Date == last_oncall_date[None])

    return (person(Person)) & \
           date_cond & \
           (Dow == get_dow(Date)) & \
           (Score == score[Date, Person]) & \
           initial_score(Person, Initial) & \
           (Oncall == count_oncall[Date, Person]) & \
           (Unavailable == count_unavailable[Date, Person]) & \
           (Onhols == count_onhols[Date, Person]) & \
           (Status == status[Date, Person])


def schedule(from_date=None, to_date=None, no_status=False, no_score=False):
    query = oncall_date(Date) & (Dow == get_dow(Date)) & is_oncall(Date, Person)

    if from_date:
        query &= (Date >= from_date)
    if to_date:
        query &= (Date <= to_date)

    status_vars = {pp: pdl.Variable('STATUS-' + pp) for (pp,) in person(Person).data}
    score_vars = {pp: pdl.Variable('SCORE-' + pp) for (pp,) in person(Person).data}
    for (pp,) in sorted(person(Person).data):
        if not no_status:
            query &= (status_vars[pp] == status[Date, pp])
        if not no_score:
            query &= (score_vars[pp] == score[Date, pp])

    return query


def dump_facts():
    m = Logic(True)
    for v in sorted(m.Db.values(), key=str):
        if v.name[0] in 'abcdefghijklmnopqrstuvwxyz' and '==' not in v.name:
            for c in v.db.values():
                if not c.body:
                    print('+', c.head)


@for_pdl
def get_dow(date):
    dd = datetime.datetime.strptime(date, '%Y%m%d')
    return dd.strftime('%a')


@for_pdl
def get_wfh_list(person):
    return ' '.join([_[0] for _ in sorted(wfh_day(person, Dow).data)])


@for_pdl
def get_unavailable_list(date):
    return ' '.join([_[0] for _ in sorted(is_unavailable(date, Person).data)])


@for_pdl
def get_onhols_list(date):
    return ' '.join([_[0] for _ in sorted(is_onhols(date, Person).data)])


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

def reinit_pdl_vars():
    global Date, Dow, Person, Name, Initial, Score, X, Y, Z

    Date = pdl.Variable('DATE')
    Dow = pdl.Variable('DOW')
    Person = pdl.Variable('PERSON')
    Name = pdl.Variable('NAME')
    Initial = pdl.Variable('INITIAL_SCORE')
    Score = pdl.Variable('SCORE')
    X = pdl.Variable('X')
    Y = pdl.Variable('Y')
    Z = pdl.Variable('Z')


def reinit_pdl_facts():
    global person
    person = pdl.Term('person')

    global person_name
    person_name = pdl.Term('person_name')

    global initial_score
    initial_score = pdl.Term('initial_score')

    global wfh_day
    wfh_day = pdl.Term('wfh_day')

    global is_oncall
    is_oncall = pdl.Term('is_oncall')
    + is_oncall(DUMMY_DATE, None)

    global is_onhols
    is_onhols = pdl.Term('is_onhols')
    + is_onhols(DUMMY_DATE, None)

    global is_unavailable
    is_unavailable = pdl.Term('is_unavailable')
    + is_unavailable(DUMMY_DATE, None)


def reinit_pdl_predicates():
    global oncall_date
    oncall_date = pdl.Term('oncall_date')
    oncall_date(Date) <= (is_oncall(Date, X) & (Date != DUMMY_DATE))

    global is_back_from_hols
    PrevDate = pdl.Variable('PrevDate')
    is_back_from_hols = pdl.Term('is_back_from_hols')
    is_back_from_hols(Date, Person) <= (
        ~is_onhols(Date, Person) &
        (PrevDate == prev_weekday(Date)) &
        is_onhols(PrevDate, Person)
    )

    global is_at_home
    is_at_home = pdl.Term('is_at_home')
    + is_at_home(None, None)
    # TODO: Use wfh_day instead
    is_at_home(Date, Person) <= ((Person == 'orbang') & (get_dow(Date).in_(['Fri'])))
    is_at_home(Date, Person) <= ((Person == 'nespor') & (get_dow(Date).in_(['Tue', 'Thu'])))


def reinit_pdl_functions():
    # The order in which the different possible cases for one function is defined matters. PDL search for an applicable
    # definition from the last definition to the first. So catch all definitions, etc should be defined first.

    global status
    status = pdl.Term('status')
    status[Date, Person] = '-'
    (status[Date, Person] == 'At home') <= (is_at_home(Date, Person))
    (status[Date, Person] == 'On hols') <= (is_onhols(Date, Person))
    (status[Date, Person] == 'Unavailable') <= (is_unavailable(Date, Person))
    (status[Date, Person] == 'Back from hols') <= (is_back_from_hols(Date, Person))
    (status[Date, Person] == 'Oncall') <= (is_oncall(Date, Person))

    global count_oncall
    count_oncall = pdl.Term('count_oncall')
    count_oncall[Date, Person] = 0
    (count_oncall[Date, Person] == _len(X)) <= (is_oncall(X, Person) & (X <= Date))

    global count_onhols
    count_onhols = pdl.Term('count_onhols')
    count_onhols[Date, Person] = 0
    (count_onhols[Date, Person] == _len(X)) <= (is_onhols(X, Person) & (X <= Date))

    global count_unavailable
    count_unavailable = pdl.Term('count_unavailable')
    count_unavailable[Date, Person] = 0
    (count_unavailable[Date, Person] == _len(X)) <= (is_unavailable(X, Person) & (X <= Date))

    global score
    score = pdl.Term('score')
    tmp = pdl.Term('tmp')
    (tmp[Person] == Initial) <= initial_score(Person, Initial)
    score[Date, Person] = (tmp[Person] + count_oncall[Date, Person] + 0.2 * count_onhols[Date, Person])

    global last_oncall_date
    last_oncall_date = pdl.Term('last_oncall_date')
    (last_oncall_date[Person] == _max(Date, order_by=Date)) <= (is_oncall(Date, Person))
    (last_oncall_date[None] == _max(Date, order_by=Date)) <= (is_oncall(Date, X) & (Date > DUMMY_DATE))

    global next_oncall_date
    next_oncall_date = pdl.Term('next_oncall_date')
    next_oncall_date[Date] = (next_weekday(Date))
    next_oncall_date[None] = (next_weekday(last_oncall_date[None]))

    global next_oncall_person
    next_oncall_person = pdl.Term('next_oncall_person')
    (next_oncall_person[Date] == _min(Person, order_by=Score)) <= (
        person(Person) &
        ~is_onhols(Date, Person) &
        ~is_unavailable(Date, Person) &
        ~is_back_from_hols(Date, Person) &
        ~is_at_home(Date, Person) &
        (Score == score[Date, Person]))


def reinit_pdl(file):
    reinit_pdl_vars()
    reinit_pdl_facts()
    read_facts_from_file(file)
    reinit_pdl_predicates()
    reinit_pdl_functions()


def read_facts_from_file(path):
    #     CSV = '''
    # # ...
    #
    # DATE,ONCALL,ONHOLS,UNAVAILABLE
    # 20171120,Alan,,
    # 20171121,Bert,,
    # 20171122,Cloe,Alan Bert,
    # 20171123,Alan,,
    # 20171124,Bert,,Cloe
    # 20171127,Bert,,Cloe
    # 20171128,Alan,,Cloe
    # 20171129,Bert,,Cloe
    # 20171130,Alan,,Cloe
    # 20171201,Alan,Bert,
    # 20171204,Cloe,Bert,
    # 20171205,Cloe,Bert,
    # 20171206,Cloe,Bert,
    # 20171207,Cloe,Bert,
    # 20171208,Alan,Bert,
    # 20171211,Cloe,Bert,
    # 20171212,Cloe,,Alan
    #     '''
    #
    #     f = StringIO(unicode(CSV))

    global file_header_lines
    file_header_lines = []

    with open(path, 'r') as f:
        in_person_section = False
        in_date_section = False

        for row in csv.reader(f, delimiter='|'):
            # Strip the leading and trailing spaces in each value.
            row = [_.strip() for _ in row]

            # Skip the empty lines.
            if len(row) == 0 or row[0] == '':
                continue

            # Collect all the comment lines so that they are preserved when the file is regenerated.
            if row[0].startswith('#'):
                file_header_lines.append(','.join(row))
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
            if in_person_section and len(row) >= 4:
                person_, name_, initial_score_, wfh_days_ = row[:4]
                + person(person_)
                + person_name(person_, name_)
                + initial_score(person_, float(initial_score_))
                if wfh_days_:
                    for d in wfh_days_.split(' '):
                        + wfh_day(person_, d)
            elif in_date_section and len(row) >= 5:
                date_, dow_, oncall_, unavailable_, onhols_ = row[:5]
                if oncall_:
                    + is_oncall(date_, oncall_)
                if unavailable_:
                    for p in unavailable_.split(' '):
                        + is_unavailable(date_, p)
                if onhols_:
                    for p in onhols_.split(' '):
                        + is_onhols(date_, p)


def write_facts_to_file(path=None):
    f = open(path, 'w') if path else sys.stdout

    global file_header_lines
    print('\n'.join(file_header_lines), file=f)
    print(file=f)
    print(file=f)

    Days = pdl.Variable('RECURRING_WFH_DAYS')
    display(person_name(Person, Name) & initial_score(Person, Initial) & (Days == get_wfh_list(Person)), file=f)
    print(file=f)

    Oncall = pdl.Variable('ONCALL')
    Unavailable = pdl.Variable('UNAVAILABLE')
    Holidays = pdl.Variable('HOLIDAYS')
    display(
        oncall_date(Date) &
        (Dow == get_dow(Date)) &
        is_oncall(Date, Oncall) &
        (Unavailable == get_unavailable_list(Date)) &
        (Holidays == get_onhols_list(Date)),
        file=f
    )


def assign_next():
    LastDate = pdl.Variable('Last Date')
    NextDate = pdl.Variable('Next Date')

    date_qry = (LastDate == last_oncall_date[None]) & (NextDate == next_oncall_date[LastDate])

    res = date_qry & (Person == next_oncall_person[NextDate])
    if res:
        last_date, next_date, next_person = res.v()
        + is_oncall(next_date, next_person)
    else:
        res = date_qry
        last_date, next_date = res.v()
        print('ERROR: Could not find a solution for {}!'.format(next_date))
        print()
        display(stats(last_date))
        display(stats(next_date))
        sys.exit(1)


def assign_until(date):
    while is_oncall(date, Person).data == []:
        assign_next()


#
# Command line interface
#

@group(context_settings=dict(terminal_width=200), help='Manage our support rota.')
@option('-f', '--file', default='./support.txt', show_default=True,
        help='The CSV file used to keep track of assignments, holidays, etc.')
@pass_context
def cli(ctx, file):
    reinit_pdl(file)
    ctx.obj = dict(file=file)


# Manages support days.
#
# Usage:
#     support show [options]
#     support assign [options]
#     support balances [options] [<date>]
#     support schedule [options] [<days-ahead> [<date>]]
#     support pollchange [options]
#     support server [options]
#     support -h | --help
#
# Actions:
#     show                    Show the current support assignment.
#     assign                  Assign a support person for the next weekday and optionally save that to the data file and mail out notification.
#     balances                Print how much support each person has done up to give date (default today).
#     schedule                Print expected assignments for the next 5 week days after give date (default today).
#     pollchange              Send a mail to the given recipients if the assignee for the next weekday has changed since the last mail.
#     server                  Start http server to serve the file
#
# Arguments:
#     <date>                  Date for which to act, in YYYYMMDD format.
#     <days-ahead>            Show schedule for this many days after <date>. Default: 10
#
# Options:
#    -h --help                Show this screen.
#    -f --file=<file>         Data file. [default: /data/cbtech/dev/support.csv]
#    -w --write               Write a new assignment to the file. [default: False]
#    -m --mail=<recipients>   Comma-separated list of recipients to whom to mail a change.


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
    assign_until(to_date)
    for date in date_range(from_date, to_date):
        res = is_oncall(date, Person).v()
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
    assign_until(to_date)
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
    assign_until(to_date)
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


@cli.command(help='Run the unit tests (development only).')
@pass_obj
def tests(obj):
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCLI)
    unittest.TextTestRunner(verbosity=2).run(suite)


#
# Unit tests
#

class TestCLI(unittest.TestCase):
    def test_print_sample_file(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['print-sample-file'])
        self.assertTrue(result.exit_code == 0)
        self.assertIn('#', result.output)
        self.assertIn('PERSON', result.output)
        self.assertIn('DATE', result.output)


#
# Main
#

if __name__ == '__main__':
    # To define the aggregate functions (eg len_, min_) and link PDL to the functions that are decorated with @for_pdl.
    pdl.create_terms(*for_pdl.registered_funcs)

    cli()
