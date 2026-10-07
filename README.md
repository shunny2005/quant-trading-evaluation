# Systematic ETF Strategy: Evaluation and Robustness Audit

Results and audit tables for a rules-based, multi-asset ETF trading strategy, published
together with the evaluation code that produced the metrics. The strategy itself is
deliberately not in this repository (see [What is withheld](#what-is-withheld)).

Research only. Everything here is a historical backtest, not live trading results and not
investment advice.

## Headline result

Fixed rules, evaluated over 2016-01-01 to 2025-12-31, net of modeled transaction costs
(0.10% of traded notional), on dividend-adjusted daily closes.

| | Total return | Annualized | Volatility | Sharpe | Max drawdown |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Strategy** | **467.46%** | **19.01%** | 20.52% | **0.93** | -30.01% |
| SPY | 294.66% | 14.75% | 18.01% | 0.82 | -33.72% |
| 1.20x SPY | 399.40% | 17.49% | 21.61% | 0.81 | -39.40% |
| SPY levered to the strategy's volatility | 365.59% | 16.67% | 20.52% | 0.81 | -37.71% |

Over the same window the strategy had a beta of 0.83 to SPY, a correlation of 0.72, and
beat SPY in 6 of 10 calendar years.

Source: [`results/summary_metrics.csv`](results/summary_metrics.csv),
[`results/beta_alpha_capture_vs_spy.csv`](results/beta_alpha_capture_vs_spy.csv).

### Read this before the number

- **The strategy is leveraged and can short.** Gross exposure averaged roughly 2x capital
  and is capped. Comparing it to unlevered SPY alone would flatter it, which is why the
  levered and volatility-matched SPY rows are in the table.
- **Financing is not in the headline.** The backtest charges transaction costs but no margin
  interest or borrow fees. The financing stress below shows how much that matters.
- **The window is holdout-style, not a pristine holdout.** Some of the research that led to
  the final rules overlapped 2016-2025, so this is a fixed-rule evaluation window rather
  than a pre-registered out-of-sample test.
- Sharpe assumes a zero risk-free rate. Taxes, slippage beyond the flat cost, and
  distribution timing are not modeled.

## Calendar-year returns

| Year | Strategy | SPY | 1.20x SPY |
| --- | ---: | ---: | ---: |
| 2016 | 4.0% | 12.0% | 14.3% |
| 2017 | 37.9% | 21.7% | 26.5% |
| 2018 | -6.7% | -4.6% | -5.8% |
| 2019 | 34.0% | 31.2% | 38.3% |
| 2020 | 6.8% | 18.3% | 20.7% |
| 2021 | 49.4% | 28.7% | 35.1% |
| 2022 | -17.4% | -18.2% | -21.9% |
| 2023 | 19.8% | 26.2% | 31.9% |
| 2024 | 51.2% | 24.9% | 30.3% |
| 2025 | 32.5% | 17.7% | 21.1% |

The result is concentrated: the widest margins over SPY came in 2017, 2021, and 2024,
and the strategy trailed SPY in 2016, 2018, 2020, and 2023. Years back to 2005 are in
[`results/yearly_returns.csv`](results/yearly_returns.csv).

## Attempts to break the result

The audit was written to disprove the result, not to improve it. No rule or weight was
changed in response to any of these tests. They run on the full 2005-2025 history, where the
same fixed rules returned 3005% net (17.8% annualized, 0.91 Sharpe, -30.0% max drawdown)
against 736% for SPY and 1066% for 1.20x SPY.

| Test | Finding | Table |
| --- | --- | --- |
| Transaction cost raised from 0.10% to 0.25%, 0.50%, 1.00% | Still ahead of SPY and 1.20x SPY at 0.50%. **Fails to beat SPY at 1.00%.** | [`transaction_cost_stress.csv`](results/transaction_cost_stress.csv) |
| Financing charged at 2%, 4%, 6% a year on gross exposure above 1x | Total return falls from 3005% to 779% at 6%. Still ahead of SPY, **behind 1.20x SPY at 6%.** | [`financing_stress.csv`](results/financing_stress.csv) |
| Signals delayed an extra 1, 2, 5 trading days | Return falls to 2291% at 5 days and max drawdown deepens to -40.7%. Still ahead of SPY. | [`signal_delay_stress.csv`](results/signal_delay_stress.csv) |
| Best 1 to 5 strategy years removed | Ahead of SPY and 1.20x SPY in every case. | [`drop_best_years.csv`](results/drop_best_years.csv) |
| Crisis years and the best 1, 3, 6, 12-month stretches removed | Ahead of SPY and 1.20x SPY in every case. | [`period_removal_tests.csv`](results/period_removal_tests.csv) |
| All twelve rolling 10-year windows from 2005-2014 to 2016-2025 | Ahead of SPY in 12 of 12, volatility-matched SPY in 11 of 12, 1.20x SPY in 9 of 12. | [`rolling_10yr_windows.csv`](results/rolling_10yr_windows.csv) |

The honest summary: the result survives moderate stress and is not explained by a single
year, a single crisis, or leverage alone. It does not survive punitive cost assumptions, and
realistic financing removes a large share of the edge over a levered index.

### Leakage controls

- A target position dated `t` earns returns from `t+1` onward
  ([`evaluation/backtest.py`](evaluation/backtest.py), tested in
  [`tests/test_backtest_timing.py`](tests/test_backtest_timing.py)).
- Signal normalization for each calendar year is fitted only on data ending before that year.
- Volatility estimates feed the next day's position, never the same day's P/L.
- Turnover is the absolute change in target position, so costs scale with leverage.
- Missing returns are not forward-filled and contribute no P/L.
- Strategy and benchmarks use the same adjusted-close return series.

Not every instrument has price history back to 2005, so the earliest years of the long
history trade the instruments available at the time. The 2016-2025 headline window is not
affected.

## What is in this repository

| Path | Contents |
| --- | --- |
| `results/` | Aggregate result tables: summary metrics, calendar-year returns, rolling windows, beta/alpha and capture versus SPY, and the stress tests above. Returns are decimals (4.674589 = 467.4589%). |
| `evaluation/metrics.py` | Return, volatility, Sharpe, drawdown, levered and volatility-matched benchmarks, beta/alpha regression, upside/downside capture |
| `evaluation/backtest.py` | The position-to-return accounting: one-day position lag, turnover, transaction costs |
| `tests/` | Tests for the code above, plus consistency checks on the published tables (for example, that the calendar-year returns compound to the headline figure) |

## What is withheld

Everything that determines what the strategy trades and how much:

- the signal rules, their parameters, and how they are combined
- rule weights and instrument weights
- the instrument universe
- the risk target, position caps, and sizing formula
- positions, exposures, forecasts, and any per-instrument or per-rule attribution
- daily return and equity series (published at calendar-year resolution only)
- the research history and the variants that were tested and rejected

At a high level, the private system computes rule-based signals on a small basket of liquid
US-listed ETFs spanning several asset classes, normalizes them walk-forward, and converts
them into volatility-targeted long/short positions that are rebalanced daily.

Consequences for this repository:

- The backtest cannot be re-run from here. Results are published as outputs.
- `evaluation/backtest.py` is a standalone version of the private accounting step with the
  project-specific configuration removed.
- The strategy is referred to only as `strategy`.

## Running the tests

Python 3.9 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
```

## Data source

Daily adjusted closes from Yahoo Finance. Figures were last regenerated on 2026-10-06.

All rights reserved. This repository is published for review; no license is granted to use
the strategy or its results.
