import numpy as np
import pandas as pd

from evaluation.backtest import run_backtest

DATES = pd.to_datetime(["2020-01-01", "2020-01-02"])


def test_backtest_uses_prior_day_position_for_returns():
    returns = pd.DataFrame({"AAA": [0.10, 0.20]}, index=DATES)
    positions = pd.DataFrame({"AAA": [1.0, 0.0]}, index=DATES)
    curve = run_backtest(returns, positions)
    assert curve["gross_strategy_return"].iloc[0] == 0.0
    assert np.isclose(curve["gross_strategy_return"].iloc[1], 0.20)


def test_same_day_signal_cannot_earn_same_day_return():
    returns = pd.DataFrame({"AAA": [0.0, 0.50]}, index=DATES)
    positions = pd.DataFrame({"AAA": [0.0, 1.0]}, index=DATES)
    curve = run_backtest(returns, positions)
    assert np.allclose(curve["gross_strategy_return"], 0.0)


def test_transaction_cost_tracks_position_change():
    returns = pd.DataFrame({"AAA": [0.0, 0.0]}, index=DATES)
    positions = pd.DataFrame({"AAA": [0.0, 2.5]}, index=DATES)
    curve = run_backtest(returns, positions, cost_per_turnover=0.01)
    assert np.isclose(curve["daily_turnover"].iloc[1], 2.5)
    assert np.isclose(curve["transaction_cost"].iloc[1], 0.025)
    assert np.isclose(curve["net_strategy_return"].iloc[1], -0.025)


def test_missing_returns_do_not_create_profit():
    returns = pd.DataFrame({"AAA": [np.nan, np.nan]}, index=DATES)
    positions = pd.DataFrame({"AAA": [3.0, 3.0]}, index=DATES)
    curve = run_backtest(returns, positions)
    assert np.allclose(curve["gross_strategy_return"], 0.0)


def test_short_position_profits_from_negative_return():
    returns = pd.DataFrame({"AAA": [0.0, -0.10]}, index=DATES)
    positions = pd.DataFrame({"AAA": [-1.0, -1.0]}, index=DATES)
    curve = run_backtest(returns, positions)
    assert np.isclose(curve["gross_strategy_return"].iloc[1], 0.10)
    assert np.isclose(curve["gross_exposure"].iloc[1], 1.0)
    assert np.isclose(curve["net_exposure"].iloc[1], -1.0)
