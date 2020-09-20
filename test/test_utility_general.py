import sys
import time
import unittest
from typing import Text, Sequence

from jiig.utility.general import apply_time_delta_string


# Used https://timeanddate.com to cross-check calculations
# TODO: Improve tests to cover more edge cases.

class TestTimeDelta(unittest.TestCase):

    @classmethod
    def timetuple(cls, tt: Sequence) -> time.struct_time:
        if len(tt) < 6:
            tt = list(tt) + ([0] * (6 - len(tt)))
        return time.struct_time((tt[0], tt[1], tt[2], tt[3], tt[4], tt[5], 0, 0, -1))

    @classmethod
    def timestamp(cls, tt: Sequence):
        return time.mktime(cls.timetuple(tt))

    @classmethod
    def compare(cls, tr: time.struct_time, te: time.struct_time) -> bool:
        ttr = tr[:6]
        tte = te[:6]
        if ttr != tte:
            # Provide more useful info than the assertTrue() gives in the calling test.
            sys.stderr.write(f'\nMISMATCH: result={ttr} expect={tte}\n')
        return ttr == tte

    @classmethod
    def check(cls, tt_start_in: Sequence, delta: Text, tt_expect_in: Sequence, negative: bool = False) -> bool:
        return cls.compare(
            apply_time_delta_string(delta, start_time=cls.timetuple(tt_start_in), negative=negative),
            cls.timetuple(tt_expect_in))

    def test_small_fwd(self):
        self.assertTrue(self.check((2000, 2, 5, 0, 0, 0), '5d', (2000, 2, 10, 0, 0, 0)))

    def test_small_bkd(self):
        self.assertTrue(self.check((2000, 2, 5, 0, 0, 0), '-5d', (2000, 1, 31, 0, 0, 0)))

    def test_small_neg(self):
        self.assertTrue(self.check((2000, 2, 5, 0, 0, 0), '5d', (2000, 1, 31, 0, 0, 0), negative=True))

    def test_small_mix_1(self):
        self.assertTrue(self.check((2000, 2, 5, 0, 0, 0), '5d,-10d', (2000, 1, 31, 0, 0, 0)))

    def test_small_mix_2(self):
        self.assertTrue(self.check((2000, 2, 5, 0, 0, 0), '105d,-110d', (2000, 1, 31, 0, 0, 0)))

    def test_large_1_fwd(self):
        self.assertTrue(self.check((2014, 4, 8, 0, 0, 0), '5y,9m,28d', (2020, 2, 5, 0, 0, 0)))

    def test_large_1_bkd(self):
        # It needs -27 days instead of -28 to get the same start date as above
        # due to 2020 being a leap year, and the calculation always applies y/m
        # adjustments before d/H/M/S.
        self.assertTrue(self.check((2020, 2, 5, 0, 0, 0), '-5y,-9m,-27d', (2014, 4, 8, 0, 0, 0)))

    def test_large_1_neg(self):
        # See comment above explaining why 27d is used instead of the original 28d.
        self.assertTrue(self.check((2020, 2, 5, 0, 0, 0), '5y,9m,27d', (2014, 4, 8, 0, 0, 0), negative=True))
