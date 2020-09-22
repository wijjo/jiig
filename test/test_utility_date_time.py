import time
import unittest
from typing import Text, Sequence, Tuple, Optional

from jiig.utility.date_time import apply_date_time_delta_string, parse_date_time


CUR_TS = time.localtime()


# Used https://timeanddate.com to cross-check calculations
# TODO: Improve tests to cover more edge cases.

class TestTimeDelta(unittest.TestCase):

    @staticmethod
    def assertApplyDelta(tt_start: Sequence,
                         delta: Text,
                         tt_expect: Sequence,
                         negative: bool = False
                         ):
        if len(tt_start) < 6:
            tt_start = list(tt_start) + ([0] * (6 - len(tt_start)))
        tt_start2 = time.struct_time((tt_start[0],
                                      tt_start[1],
                                      tt_start[2],
                                      tt_start[3],
                                      tt_start[4],
                                      tt_start[5],
                                      0, 0, -1))
        tt_result = apply_date_time_delta_string(delta,
                                                 start_time=tt_start2,
                                                 negative=negative)[:6]
        if tt_result[:6] != tt_expect[:6]:
            raise AssertionError(f'Delta result mismatch: result={tt_result[:6]} expect={tt_expect[:6]}')

    def test_small_fwd(self):
        self.assertApplyDelta((2000, 2, 5, 0, 0, 0), '5d', (2000, 2, 10, 0, 0, 0))

    def test_small_bkd(self):
        self.assertApplyDelta((2000, 2, 5, 0, 0, 0), '-5d', (2000, 1, 31, 0, 0, 0))

    def test_small_neg(self):
        self.assertApplyDelta((2000, 2, 5, 0, 0, 0), '5d', (2000, 1, 31, 0, 0, 0), negative=True)

    def test_small_mix_1(self):
        self.assertApplyDelta((2000, 2, 5, 0, 0, 0), '5d,-10d', (2000, 1, 31, 0, 0, 0))

    def test_small_mix_2(self):
        self.assertApplyDelta((2000, 2, 5, 0, 0, 0), '105d,-110d', (2000, 1, 31, 0, 0, 0))

    def test_large_1_fwd(self):
        self.assertApplyDelta((2014, 4, 8, 0, 0, 0), '5y,9m,28d', (2020, 2, 5, 0, 0, 0))

    def test_large_1_bkd(self):
        # It needs -27 days instead of -28 to get the same start date as above
        # due to 2020 being a leap year, and the calculation always applies y/m
        # adjustments before d/H/M/S.
        self.assertApplyDelta((2020, 2, 5, 0, 0, 0), '-5y,-9m,-27d', (2014, 4, 8, 0, 0, 0))

    def test_large_1_neg(self):
        # See comment above explaining why 27d is used instead of the original 28d.
        self.assertApplyDelta((2020, 2, 5, 0, 0, 0), '5y,9m,27d', (2014, 4, 8, 0, 0, 0), negative=True)


class TestParseDateTime(unittest.TestCase):

    @staticmethod
    def assertGoodDate(sin: Text, te: Tuple):
        tr = parse_date_time(sin)[:6]
        te = (te[0], te[1], te[2], 0, 0, 0)
        if tr != te:
            raise AssertionError(f'Parsed date mismatch: input={sin} result={tr} expect={te}')

    @staticmethod
    def assertGoodTime(sin: Text, te: Tuple):
        tr = parse_date_time(sin)[:6]
        te = (CUR_TS.tm_year, CUR_TS.tm_mon, CUR_TS.tm_mday, te[0], te[1], te[2])
        if tr != te:
            raise AssertionError(f'Parsed time mismatch: input={sin} result={tr} expect={te}')

    @staticmethod
    def assertGoodDateTime(sin: Text, te: Tuple):
        tr = parse_date_time(sin)[:6]
        if tr != te:
            raise AssertionError(f'Parsed date-time mismatch: input={sin} result={tr} expect={te}')

    @staticmethod
    def assertEmpty(sin: Optional[Text]):
        if parse_date_time(sin) is not None:
            raise AssertionError(f'Parsed empty error: input={sin}')

    @staticmethod
    def assertBad(sin: Text):
        if parse_date_time(sin, quiet=True) is not None:
            raise AssertionError(f'Parsed bad error: input={sin}')

    def test_empty(self):
        self.assertEmpty(None)
        self.assertEmpty('')
        self.assertEmpty(' ')

    def test_no_year(self):
        self.assertGoodDate('12-25', (CUR_TS.tm_year, 12, 25))

    def test_full_year(self):
        self.assertGoodDate('2019-12-25', (2019, 12, 25))

    def test_full_time(self):
        self.assertGoodTime('10:11:12', (10, 11, 12))

    def test_partial_year(self):
        self.assertGoodDate('19-12-25', (2019, 12, 25))

    def test_date_bad(self):
        self.assertBad('a-12-25')

    def test_too_many_parts(self):
        self.assertBad('12-25 12-25 12-25')

    def test_too_many_dates(self):
        self.assertBad('12-25 12-25')

    def test_good_date_time(self):
        self.assertGoodDateTime('2020-05-17 10:11:12', (2020, 5, 17, 10, 11, 12))
