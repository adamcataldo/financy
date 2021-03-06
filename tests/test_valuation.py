import pandas as pd
import pandas.testing as pd_testing
import unittest
from financy import valuation as v
import warnings


class TestValuation(unittest.TestCase):

    def test_annualize_fcf(self):
        quarterly = pd.DataFrame([1.0, 2.0, 2.0, 3.0, 2.0, 3.0, 3.0, 4.0],
                                 columns=['free_cashflow'])
        expected = pd.DataFrame([12.0, 8.0], columns=['free_cashflow'])
        pd_testing.assert_frame_equal(expected, v.annualize_fcf(quarterly))

    def test_annualize_fcf_incomplete_years(self):
        quarterly = pd.DataFrame([1.0, 2.0, 2.0, 3.0, 2.0, 3.0, 3.0, 4.0, 5.0],
                                 columns=['free_cashflow'])
        expected = pd.DataFrame([12.0, 8.0], columns=['free_cashflow'])
        pd_testing.assert_frame_equal(expected, v.annualize_fcf(quarterly))

    def test_adjusted_fcf(self):
        ocf_series = pd.Series([1.0, 2.0, 3.0, 4.0])
        capex_series = pd.Series([0.0, 5.0, 0.0, 0.0])
        expected = pd.Series([0.5, 1.0, 1.5, 2.0])
        pd_testing.assert_series_equal(expected, v.adjusted_freecashflow(ocf_series, capex_series))

    def test_value_asset_linear_regression_no_negative_valuations(self):
        x = v.value_asset_linear_regression(0, pd.Series([-1, -2, -3]), 0.03)
        self.assertTrue(x.low_valuation >= 0)
        self.assertTrue(x.high_valuation >= 0)
        self.assertTrue(x.expected_growth_rate >= -1.0)

    def test_value_asset_with_zeros(self):
        warnings.filterwarnings("error")
        v.value_asset(1000, pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 0, 0, 0, 0]), 0.03)
        warnings.resetwarnings()

    def test_value_asset_lt_1year_data(self):
        x = v.value_asset(1.0, pd.Series([1.0, 2.0, 3.0]), 0.03)
        self.assertEqual(x.expected_growth_rate, 0)
        self.assertEqual(x.low_valuation, 1.0)
        self.assertEqual(x.high_valuation, 1.0)

    def test_value_asset_gt_1year_data(self):
        x = v.value_asset(1.0, pd.Series([float(x) for x in range(1, 17)]), 0.03)
        self.assertTrue(x.low_valuation < x.high_valuation)

    def test_value_asset_lt_3year_data(self):
        x = v.value_asset(1.0, pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]), 0.03)
        self.assertTrue(x.low_valuation == x.high_valuation)

if __name__ == '__main__':
    unittest.main()


