"""Checks that the published result tables are internally consistent."""

from pathlib import Path

import numpy as np
import pandas as pd

RESULTS = Path(__file__).parents[1] / "results"
# Tables are rounded to 6 decimals, so compounded checks need some slack.
COMPOUND_TOLERANCE = 1e-4


def summary_row(series: str, window_start: int) -> pd.Series:
    summary = pd.read_csv(RESULTS / "summary_metrics.csv")
    match = summary[(summary["series"] == series) & (summary["window_start"] == window_start)]
    assert len(match) == 1
    return match.iloc[0]


def test_headline_matches_readme_precision():
    strategy = summary_row("strategy", 2016)
    spy = summary_row("spy", 2016)
    assert round(strategy["total_return"] * 100) == 467
    assert round(strategy["annualized_return"] * 100, 1) == 19.0
    assert round(strategy["sharpe_ratio"], 2) == 0.93
    assert round(strategy["max_drawdown"] * 100, 1) == -30.0
    assert round(spy["total_return"] * 100) == 295
    assert round(spy["annualized_return"] * 100, 1) == 14.8
    assert round(spy["sharpe_ratio"], 2) == 0.82


def test_yearly_returns_compound_to_summary_totals():
    yearly = pd.read_csv(RESULTS / "yearly_returns.csv").set_index("year")
    for window_start in [2016, 2005]:
        for series in ["strategy", "spy", "spy_1.20x"]:
            compounded = (1.0 + yearly.loc[window_start:2025, series]).prod() - 1.0
            expected = summary_row(series, window_start)["total_return"]
            assert np.isclose(compounded, expected, rtol=COMPOUND_TOLERANCE)


def test_rolling_window_ending_2025_equals_headline_window():
    rolling = pd.read_csv(RESULTS / "rolling_10yr_windows.csv")
    summary = pd.read_csv(RESULTS / "summary_metrics.csv")
    last_window = rolling[rolling["window_start"] == 2016].reset_index(drop=True)
    headline = summary[summary["window_start"] == 2016].reset_index(drop=True)
    pd.testing.assert_frame_equal(last_window, headline)


def test_vol_matched_benchmark_has_strategy_volatility():
    rolling = pd.read_csv(RESULTS / "rolling_10yr_windows.csv")
    wide = rolling.pivot(index="window_start", columns="series", values="annualized_volatility")
    assert np.allclose(wide["spy_vol_matched"], wide["strategy"], atol=1e-6)


def test_stress_baselines_equal_full_period_result():
    full_period = summary_row("strategy", 2005)["total_return"]
    cost = pd.read_csv(RESULTS / "transaction_cost_stress.csv")
    financing = pd.read_csv(RESULTS / "financing_stress.csv")
    delay = pd.read_csv(RESULTS / "signal_delay_stress.csv")
    assert np.isclose(cost.loc[cost["cost_per_unit_turnover"] == 0.001, "total_return"].iloc[0], full_period)
    assert np.isclose(
        financing.loc[financing["annual_financing_rate_on_gross_above_1x"] == 0.0, "total_return"].iloc[0],
        full_period,
    )
    assert np.isclose(delay.loc[delay["extra_delay_days"] == 0, "total_return"].iloc[0], full_period)


def test_higher_costs_and_financing_never_help():
    for filename in ["transaction_cost_stress.csv", "financing_stress.csv"]:
        table = pd.read_csv(RESULTS / filename)
        assert table["total_return"].is_monotonic_decreasing


def test_beats_spy_flags_agree_with_summary():
    spy = summary_row("spy", 2005)["total_return"]
    spy_120 = summary_row("spy_1.20x", 2005)["total_return"]
    for filename in ["transaction_cost_stress.csv", "financing_stress.csv"]:
        table = pd.read_csv(RESULTS / filename)
        assert ((table["total_return"] > spy) == table["beats_spy"]).all()
        assert ((table["total_return"] > spy_120) == table["beats_spy_120"]).all()


def test_only_aggregate_tables_are_published():
    for path in RESULTS.glob("*.csv"):
        assert len(pd.read_csv(path)) <= 48, f"{path.name} is larger than any aggregate table should be"
