from __future__ import print_function

import operator
import unittest
from math import exp, log

from functional import seq


def my_round(x):
    return round(x, 2)


def assert_almost_equal(a, b):
    assert my_round(a) == my_round(b)


# interest_rate =
#     real_free_risk_interest_rate
#   + inflation_premium
#   + default_risk_premium
#   + liquidity_premium
#   + maturity_premium


# nominal_risk_free_interest_rate = real_free_risk_interest_rate + inflation_premium
#
# Represented by:
# - US: 90-day US Treasury Bill (T-Bill)
# - FR: BTF (Bond do Trésor è Taux Fixe) - maturity up to one year
# - JP: Treasury Bill - maturity of 6 and 12 months
# - ...

def pv_factor(r, n, freq=1, cont=False):
    """

    :param r:  The interest rate per period
    :param n:  The number of periods
    :param freq:  The frequency of compounding per period
    :param cont:  Use continuous compounding if True
    :return:   The present value factor
    """
    return 1.0 / fv_factor(r, n, freq, cont)


def fv_factor(r, n, freq=1, cont=False):
    """

    :param r:  The interest rate per period
    :param n:  The number of periods
    :param freq:  The frequency of compounding per period
    :param cont:  Use continuous compounding if True
    :return:   The future value factor
    """
    if cont:
        return exp(r * n)
    else:
        return (1.0 + r) ** n if freq == 1 else (1.0 + r / freq) ** (n * freq)


def fv(pv, r, n, freq=1, cont=False):
    """
    Calculate the future value (FV).

    :param pv: The present value (principal)
    :param r:  The interest rate per period
    :param n:  The number of periods
    :param freq:  The frequency of compounding per period
    :param cont:  Use continuous compounding if True
    :return:   The future value
    """
    return pv * fv_factor(r, n, freq, cont)


def pv(fv, r, n, freq=1, cont=False):
    """
    Calculate the present value (PV).

    :param fv: The future value
    :param r:  The interest rate per period
    :param n:  The number of periods
    :param freq:  The frequency of compounding per period
    :param cont:  Use continuous compounding if True
    :return:   The future value
    """
    return fv * pv_factor(r, n, freq, cont)


def ear(r, freq=1, cont=False):
    """
    Calculate the effective annual rate (EAR).

    :param r:  The stated annual rate
    :param freq:  The frequency of compounding per year
    :param cont:  Use continuous compounding if True
    :return:   The future value
    """
    return fv_factor(r, 1, freq, cont) - 1


def annuity_fv(amount, r, n, due=False, freq=1, cont=False):
    """
    Calculate the future value of an annuity.

    :param amount:  The amount paid at the end of each period
    :param r:  The interest rate per period
    :param n:  The number of periods
    :param due:  Annuity due if True (aka in-advance), ordinary annuity otherwise (aka in-arrears)
    :param freq:  The frequency of compounding per period
    :param cont:  Use continuous compounding if True
    :return:   The present value of the annuity
    """
    if due:
        return sum(fv(amount, r, _, freq, cont) for _ in range(1, n + 1))
    else:
        return sum(fv(amount, r, _, freq, cont) for _ in range(0, n))


def annuity_pv(amount, r, n, due=False, freq=1, cont=False):
    """
    Calculate the present value of an annuity.

    :param amount:  The amount paid at the end of each period
    :param r:  The interest rate per period
    :param n:  The number of periods
    :param due:  Annuity due if True (aka in-advance), ordinary annuity otherwise (aka in-arrears)
    :param freq:  The frequency of compounding per period
    :param cont:  Use continuous compounding if True
    :return:   The present value of the annuity
    """
    if due:
        return sum(pv(amount, r, _, freq, cont) for _ in range(0, n))
    else:
        return sum(pv(amount, r, _, freq, cont) for _ in range(1, n + 1))


def perpetuity_pv(amount, r):
    """
    Calculate the present value of a perpetuity.

    :param amount: The amount paid at the end of each period
    :param r: The interest rate per period
    :return:
    """
    return float(amount) / r


class MyTests(unittest.TestCase):
    def test_pv_factor(self):
        self.assertAlmostEqual(pv_factor(0.1, 0), 1)
        self.assertAlmostEqual(pv_factor(0.1, 1), 0.9090909)
        self.assertAlmostEqual(pv_factor(0.1, 5), 0.6209213)
        self.assertAlmostEqual(pv_factor(0.1, 10), 0.38554328)

    def test_pv_factor_decreases_when_n_increases(self):
        self.assertGreater(pv_factor(0.1, 1), pv_factor(0.1, 2))

    def test_pv_factor_decreases_when_r_increases(self):
        self.assertGreater(pv_factor(0.1, 1), pv_factor(0.2, 1))

    def test_pv_factor_decreases_when_compounding_freq_increases(self):
        self.assertGreater(pv_factor(0.1, 1, freq=2), pv_factor(0.1, 1, freq=3))
        self.assertGreater(pv_factor(0.1, 1, freq=2), pv_factor(0.1, 1, cont=True))

    def test_pv_factor_relationship_with_fv_factor(self):
        self.assertAlmostEqual(pv_factor(0.05, 10), 1 / fv_factor(0.05, 10))
        self.assertAlmostEqual(pv_factor(0.05, -10), fv_factor(0.05, 10))

    def test_fv_factor(self):
        self.assertAlmostEqual(fv_factor(0.1, 0), 1)
        self.assertAlmostEqual(fv_factor(0.1, 1), 1.1)
        self.assertAlmostEqual(fv_factor(0.1, 5), 1.61051)
        self.assertAlmostEqual(fv_factor(0.1, 10), 2.59374246)
        self.assertLess(fv_factor(0.1, 1), fv_factor(0.1, 2))
        self.assertLess(fv_factor(0.1, 1), fv_factor(0.2, 1))
        self.assertLess(fv_factor(0.1 / 2, 1 * 2), fv_factor(0.1 / 3, 1 * 3))
        self.assertAlmostEqual(fv_factor(0.05, 10), 1 / pv_factor(0.05, 10))
        self.assertAlmostEqual(fv_factor(0.05, -10), pv_factor(0.05, 10))

    def test_fv_factor_increases_when_n_increases(self):
        self.assertLess(fv_factor(0.1, 1), fv_factor(0.1, 2))

    def test_fv_factor_increases_when_r_increases(self):
        self.assertLess(fv_factor(0.1, 1), fv_factor(0.2, 1))

    def test_fv_factor_increases_when_compounding_freq_increases(self):
        self.assertLess(fv_factor(0.1, 1, freq=2), fv_factor(0.1, 1, freq=3))
        self.assertLess(fv_factor(0.1, 1, freq=2), fv_factor(0.1, 1, cont=True))

    def test_fv_factor_relationship_with_pv_factor(self):
        self.assertAlmostEqual(fv_factor(0.05, 10), 1 / pv_factor(0.05, 10))
        self.assertAlmostEqual(fv_factor(0.05, -10), pv_factor(0.05, 10))

    def test_fv(self):
        self.assertAlmostEqual(fv(2000, 0.1, 0), 2000)
        self.assertAlmostEqual(fv(2000, 0.1, 1), 2200)

    def test_fv_increases_when_n_increases(self):
        self.assertLess(fv(1000, 0.1, 1), fv(1000, 0.1, 2))

    def test_fv_increases_when_r_increases(self):
        self.assertLess(fv(1000, 0.1, 1), fv(1000, 0.2, 1))

    def test_fv_increases_when_compounding_freq_increases(self):
        self.assertLess(fv(1000, 0.1, 1, freq=2), fv(1000, 0.1, 1, freq=3))
        self.assertLess(fv(1000, 0.1, 1, freq=2), fv(1000, 0.1, 1, cont=True))

    def test_pv(self):
        self.assertAlmostEqual(pv(2200, 0.1, 0), 2200)
        self.assertAlmostEqual(pv(2200, 0.1, 1), 2000)

    def test_pv_decreases_when_n_increases(self):
        self.assertGreater(pv(1000, 0.1, 1), pv(1000, 0.1, 2))

    def test_pv_decreases_when_r_increases(self):
        self.assertGreater(pv(1000, 0.1, 1), pv(1000, 0.2, 1))

    def test_pv_decreases_when_compounding_freq_increases(self):
        self.assertGreater(pv(1000, 0.1, 1, freq=2), pv(1000, 0.1, 1, freq=3))
        self.assertGreater(pv(1000, 0.1, 1, freq=2), pv(1000, 0.1, 1, cont=True))

    def test_ear(self):
        self.assertAlmostEqual(ear(0.05), 0.05)
        self.assertAlmostEqual(ear(0.05, freq=4), 0.0509453)
        self.assertAlmostEqual(ear(0.05, cont=True), 0.0512711)

    def test_ear_increases_when_compounding_freq_increases(self):
        self.assertLess(ear(0.05, freq=2), ear(0.05, freq=3))
        self.assertLess(ear(0.05, freq=2), ear(0.05, cont=True))

    def test_annuity_ord_fv(self):
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 1), 1000)
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 2), 2100)
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 2, freq=2), 2102.5)
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 2, freq=12), 2104.7130674)
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 10), 15937.424601000006)

    def test_annuity_ord_fv_increases_when_n_increases(self):
        self.assertLess(annuity_fv(1000, 0.1, 10), annuity_fv(1000, 0.1, 11))

    def test_annuity_ord_fv_increases_when_r_increases(self):
        self.assertLess(annuity_fv(1000, 0.1, 10), annuity_fv(1000, 0.11, 10))

    def test_annuity_ord_fv_increases_when_compounding_freq_increases(self):
        self.assertLess(annuity_fv(1000, 0.1, 10, freq=2), annuity_fv(1000, 0.1, 10, freq=3))
        self.assertLess(annuity_fv(1000, 0.1, 10, freq=2), annuity_fv(1000, 0.1, 10, cont=True))

    def test_annuity_ord_pv(self):
        self.assertAlmostEqual(annuity_pv(1000, 0.1, 10), 6144.56710570468)

    def test_annuity_ord_pv_increases_when_n_increases(self):
        self.assertLess(annuity_pv(1000, 0.1, 10), annuity_pv(1000, 0.1, 11))

    def test_annuity_ord_pv_decreases_when_r_increases(self):
        self.assertGreater(annuity_pv(1000, 0.1, 10), annuity_pv(1000, 0.11, 10))

    def test_annuity_ord_pv_decreases_when_compounding_freq_increases(self):
        self.assertGreater(annuity_pv(1000, 0.1, 10, freq=2), annuity_pv(1000, 0.1, 10, freq=3))
        self.assertGreater(annuity_pv(1000, 0.1, 10, freq=2), annuity_pv(1000, 0.1, 10, cont=True))

    def test_annuity_due_fv(self):
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 1, due=True), 1100)
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 2, due=True), 2310)
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 2, due=True, freq=2), 2318.00625)
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 2, due=True, freq=12), 2325.1040288)
        self.assertAlmostEqual(annuity_fv(1000, 0.1, 10, due=True), 17531.1670611)

    def test_annuity_due_fv_increases_when_n_increases(self):
        self.assertLess(annuity_fv(1000, 0.1, 10, due=True), annuity_fv(1000, 0.1, 11, due=True))

    def test_annuity_due_fv_increases_when_r_increases(self):
        self.assertLess(annuity_fv(1000, 0.1, 10, due=True), annuity_fv(1000, 0.11, 10, due=True))

    def test_annuity_due_fv_increases_when_compounding_freq_increases(self):
        self.assertLess(annuity_fv(1000, 0.1, 10, due=True, freq=2), annuity_fv(1000, 0.1, 10, due=True, freq=3))
        self.assertLess(annuity_fv(1000, 0.1, 10, due=True, freq=2), annuity_fv(1000, 0.1, 10, due=True, cont=True))

    def test_annuity_due_pv(self):
        self.assertAlmostEqual(annuity_pv(1000, 0.1, 10, due=True), 6759.0238163)

    def test_annuity_due_pv_increases_when_n_increases(self):
        self.assertLess(annuity_pv(1000, 0.1, 10, due=True), annuity_pv(1000, 0.1, 11, due=True))

    def test_annuity_due_pv_decreases_when_r_increases(self):
        self.assertGreater(annuity_pv(1000, 0.1, 10, due=True), annuity_pv(1000, 0.11, 10, due=True))

    def test_annuity_due_pv_decreases_when_compounding_freq_increases(self):
        self.assertGreater(annuity_pv(1000, 0.1, 10, due=True, freq=2), annuity_pv(1000, 0.1, 10, due=True, freq=3))
        self.assertGreater(annuity_pv(1000, 0.1, 10, due=True, freq=2), annuity_pv(1000, 0.1, 10, due=True, cont=True))

    def test_annuity_fv_ordinary_less_than_due(self):
        self.assertLess(annuity_fv(1000, 0.1, 10, due=False), annuity_fv(1000, 0.1, 10, due=True))

    def test_annuity_pv_ordinary_less_than_due(self):
        self.assertLess(annuity_pv(1000, 0.1, 10, due=False), annuity_pv(1000, 0.1, 10, due=True))

    def test_perpetuity_pv(self):
        self.assertAlmostEqual(perpetuity_pv(1000, 0.5), 2000)

    def test_perpetuity_pv_increases_when_amt_increases(self):
        self.assertLess(perpetuity_pv(1000, 0.5), perpetuity_pv(2000, 0.5))

    def test_perpetuity_pv_decreases_when_rate_increases(self):
        self.assertGreater(perpetuity_pv(1000, 0.1), perpetuity_pv(1000, 0.2))


class MyTests_Questions(unittest.TestCase):
    def test_q2(self):
        # A client has a $5 million portfolio and invests 5 percent of it in a money market fund projected to earn
        # 3 percent annually. Estimate the value of this portion of his portfolio after seven years.
        P = 5e6 * 0.05
        r = 0.03
        n = 7
        FV = fv(P, r, n)
        self.assertAlmostEqual(FV, 307468.47, places=2)

    def test_q3(self):
        # A client invests $500,000 in a bond fund projected to earn 7 percent annually. Estimate the value of her
        # investment after 10 years.
        P = 500000
        r = 0.07
        n = 10
        FV = fv(P, r, n)
        self.assertAlmostEqual(FV, 983575.68, places=2)

    def test_q4(self):
        # For liquidity purposes, a client keeps $100,000 in a bank account. The bank quotes a stated annual interest
        # rate of 7 percent. The bank’s service representative explains that the stated rate is the rate one would earn
        # if one were to cash out rather than invest the interest payments. How much will your client have in his
        # account at the end of one year, assuming no additions or withdrawals, using the following types of
        # compounding?
        # A. Quarterly.
        # B. Monthly.
        # C. Continuous.
        P = 100000
        rs = 0.07
        n = 1
        self.assertAlmostEqual(fv(P, rs, n, freq=4), 107185.90, places=2)
        self.assertAlmostEqual(fv(P, rs, n, freq=12), 107229.01, places=2)
        self.assertAlmostEqual(fv(P, rs, n, cont=True), 107250.82, places=2)

    def test_q5(self):
        # A bank quotes a rate of 5.89 percent with an effective annual rate of 6.05 percent. Does the bank use annual,
        # quarterly, or monthly compounding?
        ann = 0.0589
        target_ear = 0.0605
        diff = [(freq, abs(target_ear - ear(ann, freq))) for freq in [1, 4, 12]]
        freq = min(diff, key=operator.itemgetter(1))[0]
        self.assertEqual(freq, 12)

    def test_q6(self):
        # A bank pays a stated annual interest rate of 8 percent. What is the effective annual rate using the following
        # types of compounding?
        # A. Quarterly.
        # B. Monthly.
        # C. Continuous.
        rs = 0.08
        self.assertAlmostEqual(ear(rs, 4), 0.0824, places=4)
        self.assertAlmostEqual(ear(rs, 12), 0.0830, places=4)
        self.assertAlmostEqual(ear(rs, cont=True), 0.0833, places=4)

    def test_q7(self):
        # A couple plans to set aside $20,000 per year in a conservative portfolio projected to earn 7 percent a year.
        # If they make their first savings contribution one year from now, how much will they have at the end of
        # 20 years?
        a = 20000
        r = 0.07
        n = 20
        self.assertAlmostEqual(annuity_fv(a, r, n), 819909.85, places=2)

    def test_q8(self):
        # Two years from now, a client will receive the first of three annual payments of $20,000 from a small business
        # project. If she can earn 9 percent annually on her investments and plans to retire in six years, how much will
        # the three business project payments be worth at the time of her retirement?
        a = 20000
        r = 0.09
        fv4 = annuity_fv(a, r, 3)
        fv6 = fv(fv4, r, 2)
        self.assertAlmostEqual(fv6, 77894.21, places=2)

    def test_q9(self):
        # To cover the first year’s total college tuition payments for his two children, a father will make a $75,000
        # payment five years from now. How much will he need to invest today to meet his first tuition goal if the
        # investment earns 6 percent annually?
        FV = 75000
        r = 0.06
        n = 5
        PV = FV * pv_factor(r, n)
        self.assertAlmostEqual(PV, 56044.36, places=2)

    def test_q10(self):
        # A client has agreed to invest €100,000 one year from now in a business planning to expand, and she has
        # decided  to set aside the funds today in a bank account that pays 7 percent compounded quarterly. How much
        # does she need to set aside?
        FV = 100000
        r = 0.07
        n = 1
        PV = FV * pv_factor(r, n, freq=4)
        self.assertAlmostEqual(PV, 93295.85, places=2)

    def test_q11(self):
        # A client can choose between receiving 10 annual $100,000 retirement payments, starting one year from today,
        # or receiving a lump sum today. Knowing that he can invest at a rate of 5 percent annually, he has decided to
        # take the lump sum. What lump sum today will be equivalent to the future annual payments?
        a = 100000
        r = 0.05
        n = 10
        self.assertAlmostEqual(annuity_pv(a, r, n), 772173.49, places=2)

    def test_q12(self):
        # A perpetual preferred stock position pays quarterly dividends of $1,000 indefinitely (forever). If an investor
        # has a required rate of return of 12 percent per year compounded quarterly on this type of investment, how much
        # should he be willing to pay for this dividend stream?
        a = 1000
        r = 0.12 / 4
        self.assertAlmostEqual(perpetuity_pv(a, r), 33333.33, places=2)

    def test_q13(self):
        # At retirement, a client has two payment options: a 20-year annuity at €50,000 per year starting after one
        # year or a lump sum of €500,000 today. If the client’s required rate of return on retirement fund investments
        # is 6 percent per year, which plan has the higher present value and by how much?
        ann_pv = annuity_pv(50000, 0.06, 20)
        lump_pv = 500000
        if ann_pv > lump_pv:
            highest = 'annuity'
        else:
            highest = 'lump sum'
        diff = abs(ann_pv - lump_pv)
        self.assertEqual(highest, 'annuity')
        self.assertAlmostEqual(diff, 73496.06, places=2)

    def test_q14(self):
        # You are considering investing in two different instruments. The first instrument will pay nothing for three
        # years, but then it will pay $20,000 per year for four years. The second instrument will pay $20,000 for three
        # years and $30,000 in the fourth year. All payments are made at year-end. If your required rate of return on
        # these investments is 8 percent annually, what should you be willing to pay for:
        # A. The first instrument?
        # B. The second instrument (use the formula for a four-year annuity)?
        r = 0.08
        # First instrument
        first_pv = annuity_pv(20000, r, 4) * pv_factor(r, 3)
        self.assertAlmostEqual(first_pv, 52585.46, places=2)
        # Second instrument
        second_pv = annuity_pv(20000, r, 3) + pv(30000, r, 4)
        self.assertAlmostEqual(second_pv, 73592.84, places=2)

    def test_q15(self):
        # Suppose you plan to send your daughter to college in three years. You expect her to earn two-thirds of her
        # tuition payment in scholarship money, so you estimate that your payments will be $10,000 a year for four
        # years. To estimate whether you have set aside enough money, you ignore possible inflation in tuition payments
        # and assume that you can earn 8 percent annually on your investments. How much should you set aside now to
        # cover these payments?
        r = 0.08
        self.assertAlmostEqual(annuity_pv(10000, r, 4, due=False) * pv_factor(r, 2), 28396.15, places=2)
        self.assertAlmostEqual(annuity_pv(10000, r, 4, due=True) * pv_factor(r, 3), 28396.15, places=2)

    def test_q16(self):
        # A client is confused about two terms on some certificate-of-deposit rates quoted at his bank in the United
        # States. You explain that the stated annual interest rate is an annual rate that does not take into account
        # compounding within a year. The rate his bank calls APY (annual percentage yield) is the effective annual rate
        # taking into account compounding. The bank’s customer service representative mentioned monthly compounding,
        # with $1,000 becoming $1,061.68 at the end of a year. To prepare to explain the terms to your client, calculate
        # the stated annual interest rate that the bank must be quoting.
        rs = 12 * (1.06168 ** (1 / 12.0) - 1)
        self.assertAlmostEqual(rs, 0.06, places=2)

    def test_q17(self):
        # A client seeking liquidity sets aside €35,000 in a bank account today. The account pays 5 percent compounded
        # monthly. Because the client is concerned about the fact that deposit insurance covers the account for only up
        # to €100,000, calculate how many months it will take to reach that amount.
        a = (100000 / 35000.0) ** (1 / 12.0)
        b = 1 + 0.05 / 12
        n = log(a) / log(b)
        self.assertAlmostEqual(n, 21.04, places=2)

    def test_q18(self):
        # A client plans to send a child to college for four years starting 18 years from now. Having set aside money
        # for tuition, she decides to plan for room and board also. She estimates these costs at $20,000 per year,
        # payable at the beginning of each year, by the time her child goes to college. If she starts next year and
        # makes 17 payments into a savings account paying 5 percent annually, what annual payments must she make?
        r = 0.05
        out = annuity_pv(20000, r, 4)  # PV of rent annuity at t=17
        amt = out / (((1 + r) ** 17 - 1) / r)
        self.assertAlmostEqual(amt, 2744.50, places=2)

    def test_q19(self):
        # A couple plans to pay their child’s college tuition for 4 years starting 18 years from now. The current
        # annual cost of college is C$7,000, and they expect this cost to rise at an annual rate of 5 percent. In their
        # planning, they assume that they can earn 6 percent annually. How much must they put aside each year, starting
        # next year, if they plan to make 17 equal payments?
        pmt18 = fv(7000, 0.05, 18)
        pmt19 = fv(7000, 0.05, 19)
        pmt20 = fv(7000, 0.05, 20)
        pmt21 = fv(7000, 0.05, 21)

        pmt_pv_17 = pv(pmt18, 0.06, 1) + pv(pmt19, 0.06, 2) + pv(pmt20, 0.06, 3) + pv(pmt21, 0.06, 4)
        self.assertAlmostEqual(pmt_pv_17, 62677.13, places=2)
        amt = pmt_pv_17 / (((1 + 0.06) ** 17 - 1) / 0.06)
        self.assertAlmostEqual(amt, 2221.58, places=2)

    def test_q20(self):
        # You are analyzing the last five years of earnings per share data for a company. The figures are $4.00, $4.50,
        # $5.00, $6.00, and $7.00. At what compound annual rate did EPS grow during these years?
        pv = 4
        fv = 7
        n = 4.0
        r = (fv / pv) ** (1 / n) - 1
        self.assertAlmostEqual(r, 0.15, places=2)

    def test_q21(self):
        # An analyst expects that a company’s net sales will double and the company’s net income will triple over the
        # next five-year period starting now. Based on the analyst’s expectations, which of the following best describes
        # the expected compound annual growth?
        # A. Net sales will grow 15% annually and net income will grow 25% annually.
        # B. Net sales will grow 20% annually and net income will grow 40% annually.
        n = 5.0
        # Sales: 2 S = S (1 + g)^5
        sales_growth = 2 ** (1 / n) - 1
        self.assertAlmostEqual(sales_growth, 0.15, places=2)
        # Income: 3 I = I (1 + g)^5
        income_growth = 3 ** (1 / n) - 1
        self.assertAlmostEqual(income_growth, 0.25, places=2)


if __name__ == '__main__':
    n = 11
    pv = 1000
    r = 0.05

    print(seq.range(n + 1). \
          map(lambda x: (x, fv(pv, r, x))). \
          tabulate()
          )

    print()

    n = 11
    pv = 1000
    r = 0.05

    print(seq(1, 2, 4, 365, 10 * 365). \
          map(lambda x: (x, fv(pv, r, n, freq=x))). \
          tabulate()
          )

    print()

    print('{:,.2f}'.format(fv(5e6, 0.07, 5)))
    print('{:,.2f}'.format(fv(2500000, 0.08, 6)))

    # A pension fund manager estimates that his corporate sponsor will make a $10 million contribution five years from now.
    # The rate of return on plan assets has been estimated at 9 percent per year. The pension fund manager wants to
    # calculate the future value of this contribution 15 years from now, which is the date at which the funds will be
    # distributed to the retires. What is the future value?
    #
    # |_______|_______|_______|_______|_______|    ...    |
    # 0       1       2       3       4       5          15
    #                                        pv5        fv15
    pv5 = 10e6
    r = 0.09
    fv15_a = fv(pv5, r, 15 - 5)
    fv15_b = fv(fv(pv5, r, -5), r, 15)
    fv15_c = fv(pv5 / fv_factor(r, 5), r, 15)
    fv15_d = fv(pv5 * pv_factor(r, 5), r, 15)
    print('fv_a', my_round(fv15_a))
    print('fv_b', my_round(fv15_b))
    print('fv_c', my_round(fv15_c))
    print('fv_d', my_round(fv15_d))
    assert_almost_equal(fv15_a, fv15_b)
    assert_almost_equal(fv15_a, fv15_c)
    assert_almost_equal(fv15_a, fv15_d)
