from __future__ import print_function

from pyDatalog import pyDatalog as pdl


def distinct(*args):
    print(len(set(args)), len(args))
    return len(set(args)) == len(args)


def total(*args):
    return sum(args)


pdl.create_terms('distinct', 'total')

pdl.load('''
    digit(X) <= (X.in_([1, 2, 3, 4, 5, 6, 7, 8, 9]))

    print((
        digit(A) & \
        digit(B) & \
        (A < B) & \
        digit(C) & \
        (B < C) & \
        (total(A, B, C) == 18)
    ).sort())
''')
#
# pdl.load('''
#     digit(X) <= (X.in_([1, 2, 3, 4, 5, 6, 7, 8, 9]))
#
#     print((
#         digit(A) & \
#         digit(B) & \
#         digit(C) & \
#         digit(D) & \
#         digit(E) & \
#         digit(F) & \
#         digit(G) & \
#         digit(H) & \
#         digit(I) & \
#         ((A + B + C) == 15) & \
#         ((C + D + E) == 15) & \
#         ((F + G + I) == 15) & \
#         ((A + C + F) == 15) & \
#         ((B + D + G) == 15) & \
#         ((C + E + I) == 15) & \
#         ((A + D + I) == 15) & \
#         ((F + D + C) == 15)
#     ).sort())
# ''')
