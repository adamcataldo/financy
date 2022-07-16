import pandas as pd
import pandas.testing as pd_testing
import unittest
import valuation as v

class TestValuation(unittest.TestCase):

    def test_annualize_fcf(self):
        quarterly = pd.DataFrame([1.0, 2.0, 2.0, 3.0, 2.0, 3.0, 3.0, 4.0],
                              columns=['free_cashflow'])
        expected = pd.DataFrame([12.0, 8.0], columns=['free_cashflow'])
        pd_testing.assert_frame_equal(v.annualize_fcf(quarterly), expected)

if __name__ == '__main__':
    unittest.main()