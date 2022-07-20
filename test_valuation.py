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

    def test_adjusted_fcf(self):
        ocf_series = pd.Series([1.0, 2.0, 3.0, 4.0])
        capex_series = pd.Series([0.0, 5.0, 0.0, 0.0])
        expected = pd.Series([0.5, 1.0, 1.5, 2.0])
        pd_testing.assert_series_equal(v.adjusted_freecashflow(ocf_series, capex_series), expected)

if __name__ == '__main__':
    unittest.main()