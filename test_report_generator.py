from unittest import TestCase
from valuation import IntrinsicValue
import report_generator as rg


class Test(TestCase):
    def test_rate_stock_zero_low_valuation_negative_ev(self):
        iv = IntrinsicValue(0.0, 1.0, -1.0, 0.02)
        x = rg.rate_stock(iv, 'FOO')
        self.assertEqual(x[0], rg.BUY)
        self.assertEqual(x[1][2], 0.02)
