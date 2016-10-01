#!/usr/bin/python3

"""
This program shows off a python decorator which implements tail call optimization. It
does this by throwing an exception if it is it's own grandparent, and catching such
exceptions to recall the stack.
"""

import sys
import time
from contextlib import contextmanager
from functools import wraps

from nose.tools import raises

N = 10000
EXPECTED_DIGITS = 35660


@contextmanager
def timer(label):
    start = time.clock()
    yield
    end = time.clock()
    print("{} took {:.4f} seconds".format(label, end - start))


class _TailRecurseException(BaseException):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs


def tailrec(func):
    """
    This function decorates a function with tail call
    optimization. It does this by throwing an exception
    if it is it's own grandparent, and catching such
    exceptions to fake the tail call optimization.

    This function fails if the decorated
    function recurses in a non-tail context.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        frame = sys._getframe()
        if frame.f_back and frame.f_back.f_back and frame.f_back.f_back.f_code == frame.f_code:
            raise _TailRecurseException(args, kwargs)
        else:
            while True:
                try:
                    return func(*args, **kwargs)
                except _TailRecurseException as e:
                    args = e.args
                    kwargs = e.kwargs

    return wrapper


def fact_iter(n):
    acc = 1
    for i in range(1, n + 1):
        acc *= i
    return acc


def fact_rec(n):
    return 1 if n <= 0 else n * fact_rec(n - 1)


def fact_tailrec(n):
    @tailrec
    def fact(n, acc):
        return acc if n == 0 else fact(n - 1, n * acc)

    return fact(n, acc=1)


def test_iter():
    assert EXPECTED_DIGITS == len(str(fact_iter(N)))


@raises(RuntimeError)
def test_rec():
    fact_rec(N)


def test_tailrec():
    assert EXPECTED_DIGITS == len(str(fact_tailrec(N)))


if __name__ == "__main__":
    with timer("The iterative version"):
        print("fact_iter({})    ===> {:,} digits".format(N, len(str(fact_iter(N)))))

    print()

    with timer("The recursive version"):
        try:
            print("fact_rec({})     ===> {:,} digits".format(N, len(str(fact_rec(N)))))
        except RuntimeError as e:
            print("fact_rec({})     ===> {}".format(N, e))

    print()

    with timer("The tail recursive version"):
        print("fact_tailrec({}) ===> {:,} digits".format(N, len(str(fact_tailrec(N)))))
