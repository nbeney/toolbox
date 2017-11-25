# TODO: Add empty dates to file
# TODO: Schedule for next days

# This script must be updated when people join or leave the CBTech team. Search for the 'MAINTENANCE' string in this
# file to find out where changes are required.

from __future__ import print_function

import csv
import datetime
import sys
from io import StringIO

import click
from pyDatalog import Logic
from pyDatalog import pyDatalog as pdl

# For convenience only so that we can type pdl.Term later.
pdl.Term = pdl.pyParser.Term

#
# Constants
#

DUMMY_DATE = '19700101'

#
# Globals
#

# Global pyDatalog variables
Abbrev = None
Date = None
Dow = None
Person = None
Score = None
X = None
Y = None
Z = None

# Global pyDatalog facts
abbrev = None
is_oncall = None
is_onhols = None
is_unavailable = None

# Global pyDatalog predicates
person = None
oncall_date = None
is_back_from_hols = None
is_at_home = None

# Global pyDatalog functions
initial_score = None
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

def display(res, title=None):
    if title:
        print('***** ' + title + ':')
    print(res.sort())
    print()


def stats(date=None):
    Initial = pdl.Variable('Initial')
    Oncall = pdl.Variable('Oncall')
    Onhols = pdl.Variable('Onhols')
    Unavailable = pdl.Variable('Unavailable')
    Status = pdl.Variable('Status')

    date_cond = (Date == date) if date else (Date == last_oncall_date[None])

    return (person(Person)) & \
           date_cond & \
           (Dow == dow(Date)) & \
           (Score == score[Date, Person]) & \
           (Initial == initial_score[Person]) & \
           (Oncall == count_oncall[Date, Person]) & \
           (Onhols == count_onhols[Date, Person]) & \
           (Unavailable == count_unavailable[Date, Person]) & \
           (Status == status[Date, Person])


def schedule():
    status_vars = {pp: pdl.Variable('Status ' + aa) for pp, aa in abbrev(Person, Abbrev).data}
    score_vars = {pp: pdl.Variable('Score ' + aa) for pp, aa in abbrev(Person, Abbrev).data}

    res = oncall_date(Date) & (Dow == dow(Date)) & is_oncall(Date, Person)
    for pp, aa in sorted(abbrev(Person, Abbrev).data):
        res &= (status_vars[pp] == status[Date, pp]) & (score_vars[pp] == score[Date, pp])
    return res


def dump_facts():
    m = Logic(True)
    for v in sorted(m.Db.values(), key=str):
        if v.name[0] in 'abcdefghijklmnopqrstuvwxyz' and '==' not in v.name:
            for c in v.db.values():
                if not c.body:
                    print('+', c.head)


def dow(date):
    dd = datetime.datetime.strptime(date, '%Y%m%d')
    return dd.strftime('%a')


def next_weekday(date):
    dd = datetime.datetime.strptime(date, '%Y%m%d')
    dd += datetime.timedelta(days=1)
    if dd.isoweekday() in (6, 7):
        dd += datetime.timedelta(days=8 - dd.isoweekday())
    return dd.strftime('%Y%m%d')


def prev_weekday(date):
    dd = datetime.datetime.strptime(date, '%Y%m%d')
    dd += datetime.timedelta(days=-1)
    if dd.isoweekday() in (6, 7):
        dd += datetime.timedelta(days=5 - dd.isoweekday())
    return dd.strftime('%Y%m%d')


#
# Logic
#

def reinit_pdl_vars():
    global Abbrev, Date, Dow, Person, Score, X, Y, Z

    Abbrev = pdl.Variable('Abbrev')
    Date = pdl.Variable('Date')
    Dow = pdl.Variable('DOW')
    Person = pdl.Variable('Person')
    Score = pdl.Variable('Score')
    X = pdl.Variable('X')
    Y = pdl.Variable('Y')
    Z = pdl.Variable('Z')


def reinit_pdl_facts():
    global abbrev
    abbrev = pdl.Term('abbrev')
    # MAINTENANCE: Add or drop people as appropriate.
    + abbrev('Alan', 'AA')
    + abbrev('Bert', 'BB')
    + abbrev('Cloe', 'CC')

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
    global person
    person = pdl.Term('person')
    person(Person) <= abbrev(Person, Abbrev)

    global oncall_date
    oncall_date = pdl.Term('oncall_date')
    oncall_date(Date) <= (is_oncall(Date, X) & (Date != DUMMY_DATE))

    global is_back_from_hols
    PrevDate = pdl.Variable('PrevDate')
    is_back_from_hols = pdl.Term('is_back_from_hols')
    is_back_from_hols(Date, Person) <= (
        ~is_onhols(Date, Person) & (PrevDate == prev_weekday(Date)) & is_onhols(PrevDate, Person))

    global is_at_home
    is_at_home = pdl.Term('is_at_home')
    + is_at_home(None, None)
    # MAINTENANCE: Add or drop people as appropriate.
    is_at_home(Date, Person) <= ((Person == 'Alan') & (dow(Date).in_(['Mon'])))
    is_at_home(Date, Person) <= ((Person == 'Bert') & (dow(Date).in_(['Tue', 'Thu'])))
    is_at_home(Date, Person) <= ((Person == 'Cloe') & (dow(Date).in_(['Fri'])))


def reinit_pdl_functions():
    # The order in which the different possible cases for one function is defined matters. PDL search for an applicable
    # definition from the last definition to the first. So catch all definitions, etc should be defined first.

    global initial_score
    initial_score = pdl.Term('initial_score')
    # MAINTENANCE: Add or drop people as appropriate.
    initial_score['Alan'] = 0
    initial_score['Bert'] = 0
    initial_score['Cloe'] = 0

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
    score[Date, Person] = (initial_score[Person] + count_oncall[Date, Person] + 0.2 * count_onhols[Date, Person])

    global last_oncall_date
    last_oncall_date = pdl.Term('last_oncall_date')
    (last_oncall_date[Person] == _max(Date, order_by=Date)) <= (is_oncall(Date, Person))
    (last_oncall_date[None] == _max(Date, order_by=Date)) <= (is_oncall(Date, X))

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


def reinit_pdl():
    reinit_pdl_vars()
    reinit_pdl_facts()
    read_facts_from_file()
    reinit_pdl_predicates()
    reinit_pdl_functions()


def read_facts_from_file():
    CSV = '''
# ...

DATE,ONCALL,ONHOLS,UNAVAILABLE
20171120,Alan,,
20171121,Bert,,
20171122,Cloe,Alan Bert,
20171123,Alan,,
20171124,Bert,,Cloe
20171127,Bert,,Cloe
20171128,Alan,,Cloe
20171129,Bert,,Cloe
20171130,Alan,,Cloe
20171201,Alan,Bert,
20171204,Cloe,Bert,
20171205,Cloe,Bert,
20171206,Cloe,Bert,
20171207,Cloe,Bert,
20171208,Alan,Bert,
20171211,Cloe,Bert,
20171212,Cloe,,Alan
    '''

    f = StringIO(CSV)

    r = csv.reader(f)
    for row in r:
        if len(row) != 4:
            continue
        if row[0].startswith('#'):
            continue
        if row[0] == 'DATE':
            continue
        date, oncall, onhols, unavailable = row
        if oncall:
            + is_oncall(date, oncall)
        for c in onhols.split(' '):
            + is_onhols(date, c)
        for c in unavailable.split(' '):
            + is_unavailable(date, c)


def write_facts_to_file():
    def get_list(predicate, date):
        return ' '.join([_[0] for _ in sorted(predicate(date, Person).data)])

    comment = '''
# ...
# ...
# ...
# ...
# ...
    '''[1:]  # Drop the first EOL character

    f = sys.stdout
    print(comment, file=f)
    w = csv.writer(f)
    w.writerow(['DATE', 'ONCALL', 'ONHOLS', 'UNAVAILABLE'])
    for date, oncall in sorted(oncall_date(Date) & is_oncall(Date, Person)):
        onhols = get_list(is_onhols, date)
        unavailable = get_list(is_unavailable, date)
        w.writerow([date, oncall, onhols, unavailable])


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


#
# Command line interface
#

@click.group()
def cli():
    pass


@cli.command(help='Assign the next oncall person.')
def assign():
    reinit_pdl()
    display(stats())
    for x in range(50):
        assign_next()
    display(schedule())
    display(stats())
    # dump_facts()
    write_facts_to_file()


#
# Main
#

if __name__ == '__main__':
    # To define the aggregate functions (len_, min_, etc) and link PDL to some Python functions
    pdl.create_terms('dow', 'next_weekday', 'prev_weekday')

    cli()
