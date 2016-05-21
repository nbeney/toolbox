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


@contextmanager
def timer(label):
    start = time.clock()
    yield
    end = time.clock()
    print("{} took {} seconds".format(label, end - start))
    

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

# Iterative version.


def fact_iter(n):
    acc = 1
    for i in range(1, n + 1):
        acc *= i
    return acc

with timer("The iterative version"):
    print("fact_iter(10000)    ===> {:,} digits".format(len(str(fact_iter(10000)))))
print()

# Recursive version.


def fact_rec(n):
    return 1 if n <= 0 else n * fact_rec(n - 1)

try:
    with timer("The recursive version"):
        print("fact_rec(10000)     ===> {:,} digits".format(len(str(fact_rec(10000)))))
except RuntimeError as e:
    print("fact_rec(10000)     ===>", e)
print()

# Tail recursive version.


def fact_tailrec(n):
    @tailrec
    def fact(n, acc):
        return acc if n == 0 else fact(n - 1, n * acc)
    return fact(n, acc=1)

with timer("The tail recursive version"):
    print("fact_tailrec(10000) ===> {:,} digits".format(len(str(fact_tailrec(10000)))))
