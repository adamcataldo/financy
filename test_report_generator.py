from unittest import TestCase
from sources.liquidity import BidAsk
from valuation import IntrinsicValue
import report_generator as rg

class Test(TestCase):
    def test_rate_stock_missing_bid_ask(self):
        missing_bid = BidAsk(0.0, 100.0)
        missing_ask = BidAsk(100.0, 0.0)
        missing_both = BidAsk(0.0, 0.0)
        iv = IntrinsicValue(100.0, 200.0, 50.0, 0.2)
        stock = "FOO"
        missing_bid_rating = rg.rate_stock(iv, missing_bid, stock)
        missing_ask_rating = rg.rate_stock(iv, missing_ask, stock)
        missing_both_rating = rg.rate_stock(iv, missing_both, stock)
        missing_bid_liquidity = missing_bid_rating[1][6]
        missing_ask_liquidity = missing_ask_rating[1][6]
        missing_both_liquidity = missing_both_rating[1][6]
        self.assertEqual(missing_bid_liquidity, 0.5)
        self.assertEqual(missing_ask_liquidity, 0.5)
        self.assertEqual(missing_both_liquidity, 0.5)
