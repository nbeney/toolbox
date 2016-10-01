#!/usr/bin/python3

"""
Test module to play with doctest.

Use the fact function as em aexample:
>>> fact(5)
120
"""


def fact(n):
    """
    Calculate the factorial of a positive integer number.

    >>> [fact(_) for _ in range(6)]
    [1, 1, 2, 6, 24, 120]
    >>> fact(-1)
    0
    """

    return 1 if n <= 1 else n * fact(n - 1)

if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # Invoke with python3 test-doctest.py    to see only failed tests.
    # Invoke with python3 test-doctest.py -v to see all the tests.
