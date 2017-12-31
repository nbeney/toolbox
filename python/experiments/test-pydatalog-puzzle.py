from __future__ import print_function

from pyDatalog import Logic
from pyDatalog import pyDatalog as pdl

# For convenience only so that we can type pdl.Term later.
pdl.Term = pdl.pyParser.Term


def dump_all():
    m = Logic(True)
    for v in sorted(m.Db.values(), key=str):
        for c in v.db.values():
            if not c.body:
                print('+', c.head)
            else:
                print(c.head, '<=', c.body)


def make_vars(*names):
    return [pdl.Variable(_) for _ in names]


class C:
    def _save_new_logic(self):
        self._logic = Logic()

    def _restore_saved_logic(self):
        Logic(self._logic)

    def __init__(self, name, val):
        self._save_new_logic()

        self.fact = pdl.Term(name + '-fact')
        + self.fact(val)

        self.pred = pdl.Term(name + '-pred')
        X, Y = make_vars('X', 'Y')
        self.pred(X) <= self.fact(Y) & (X == 2 * Y)

    def m(self):
        self._restore_saved_logic()
        X,  = make_vars('X')
        print(self.fact(X).data)
        print(self.pred(X).data)


if __name__ == '__main__':
    g = (_ for _ in range(1, 1000))

    print('-' * 10, next(g))
    a = C('aaa', 1)
    dump_all()

    print('-' * 10, next(g))
    b = C('bbb', 2)
    dump_all()

    print('-' * 10, next(g))
    a.m()
    dump_all()

    print('-' * 10, next(g))
    b.m()
    dump_all()

    print('-' * 10, next(g))
    a.m()
    dump_all()
