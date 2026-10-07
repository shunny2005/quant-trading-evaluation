import pandas as pd

from evaluation.metrics import INITIAL_CAPITAL, calculate_drawdown


def run_backtest(
    returns: pd.DataFrame,
    positions: pd.DataFrame,
    cost_per_turnover: float = 0.0,
) -> pd.DataFrame:
    """
    Turns target positions into a daily net-return series.

    Both inputs are wide: one row per date, one column per instrument.
    Positions are fractions of capital (1.0 = 100% long, -0.5 = 50% short).

    Gross return:
        sum(yesterday's position * today's return)

    Turnover:
        sum(abs(position_today - position_yesterday))

    Cost:
        turnover * cost_per_turnover

    Net return:
        gross return - cost
    """
    returns = returns.sort_index()
    positions = positions.sort_index().fillna(0)

    common_symbols = [symbol for symbol in returns.columns if symbol in positions.columns]
    if not common_symbols:
        raise ValueError("No symbols overlap between returns and positions.")

    common_dates = returns.index.intersection(positions.index)
    returns = returns.loc[common_dates, common_symbols]
    positions = positions.loc[common_dates, common_symbols]

    # A target dated t earns returns from t+1 onward, never the same day.
    shifted_positions = positions.shift(1).fillna(0)

    # Missing returns contribute no P/L: pandas skips NaN in the row sum.
    gross_strategy_returns = (shifted_positions * returns).sum(axis=1)

    daily_turnover = positions.diff().abs().sum(axis=1).fillna(0)
    transaction_cost = daily_turnover * cost_per_turnover
    net_strategy_returns = gross_strategy_returns - transaction_cost

    net_equity = INITIAL_CAPITAL * (1.0 + net_strategy_returns).cumprod()

    return pd.DataFrame(
        {
            "gross_strategy_return": gross_strategy_returns,
            "daily_turnover": daily_turnover,
            "transaction_cost": transaction_cost,
            "net_strategy_return": net_strategy_returns,
            "net_equity": net_equity,
            "net_drawdown": calculate_drawdown(net_equity),
            "gross_exposure": shifted_positions.abs().sum(axis=1),
            "net_exposure": shifted_positions.sum(axis=1),
        }
    )
