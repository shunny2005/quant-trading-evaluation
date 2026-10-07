import numpy as np
import pandas as pd

from evaluation.metrics import (
    beta_alpha_regression,
    calculate_full_period_vol_match_leverage,
    calculate_return_metrics,
    expanding_prior_vol_matched_returns,
    leveraged_returns,
    remove_years,
    upside_downside_capture,
    vol_matched_returns,
)


def test_leveraged_returns_multiplies_daily_returns():
    returns = pd.Series([0.01, -0.02, 0.03])
    result = leveraged_returns(returns, 1.2)
    assert np.allclose(result.values, [0.012, -0.024, 0.036])


def test_vol_matched_returns_match_realized_volatility():
    strategy = pd.Series([0.02, -0.02, 0.01, -0.01])
    benchmark = pd.Series([0.01, -0.01, 0.005, -0.005])
    matched, leverage = vol_matched_returns(strategy, benchmark)
    assert np.isclose(leverage, 2.0)
    assert np.isclose(matched.std(), strategy.std())


def test_expanding_prior_vol_matched_returns_uses_prior_data():
    strategy = pd.Series([0.02, -0.02, 0.04, -0.04])
    benchmark = pd.Series([0.01, -0.01, 0.01, -0.01])
    matched = expanding_prior_vol_matched_returns(strategy, benchmark, min_periods=2)
    assert np.isclose(matched.iloc[0], benchmark.iloc[0])
    assert np.isclose(matched.iloc[1], benchmark.iloc[1])
    assert np.isclose(matched.iloc[2], benchmark.iloc[2] * 2.0)


def test_beta_alpha_regression_recovers_linear_relationship():
    benchmark = pd.Series([0.01, -0.01, 0.02, -0.02, 0.03])
    strategy = 0.001 + 1.5 * benchmark
    result = beta_alpha_regression(strategy, benchmark)
    assert np.isclose(result["beta"], 1.5)
    assert np.isclose(result["daily_alpha"], 0.001)
    assert np.isclose(result["r_squared"], 1.0)


def test_upside_downside_capture_uses_spy_up_and_down_days():
    spy = pd.Series([0.01, -0.01, 0.02, -0.02])
    strategy = pd.Series([0.02, -0.005, 0.04, -0.01])
    result = upside_downside_capture(strategy, spy)
    assert np.isclose(result["upside_capture"], 2.0)
    assert np.isclose(result["downside_capture"], 0.5)
    assert result["spy_up_days"] == 2
    assert result["spy_down_days"] == 2


def test_remove_years_excludes_requested_calendar_years():
    returns = pd.Series(
        [0.01, 0.02, 0.03],
        index=pd.to_datetime(["2020-01-02", "2021-01-04", "2022-01-03"]),
    )
    result = remove_years(returns, [2021])
    assert list(result.index.year) == [2020, 2022]


def test_calculate_return_metrics_compounds_from_initial_capital():
    returns = pd.Series([0.10, -0.05])
    result = calculate_return_metrics(returns, initial_capital=100000)
    assert np.isclose(result["total_return"], 0.045)
    assert np.isclose(result["ending_capital"], 104500)
