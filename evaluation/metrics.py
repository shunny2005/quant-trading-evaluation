import numpy as np
import pandas as pd

INITIAL_CAPITAL = 100_000
TRADING_DAYS_PER_YEAR = 252


def calculate_drawdown(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1.0


def equity_from_returns(returns: pd.Series, initial_capital: float = INITIAL_CAPITAL) -> pd.Series:
    returns = returns.fillna(0)
    return initial_capital * (1.0 + returns).cumprod()


def calculate_return_metrics(
    daily_returns: pd.Series,
    initial_capital: float = INITIAL_CAPITAL,
) -> dict:
    daily_returns = daily_returns.dropna()
    if daily_returns.empty:
        return {
            "total_return": np.nan,
            "ending_capital": np.nan,
            "pnl": np.nan,
            "annualized_return": np.nan,
            "annualized_volatility": np.nan,
            "sharpe_ratio": np.nan,
            "max_drawdown": np.nan,
        }

    equity = equity_from_returns(daily_returns, initial_capital=initial_capital)
    total_return = equity.iloc[-1] / initial_capital - 1.0
    years = len(daily_returns) / TRADING_DAYS_PER_YEAR
    annualized_return = (1.0 + total_return) ** (1.0 / years) - 1.0
    annualized_volatility = daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    sharpe_ratio = (
        annualized_return / annualized_volatility
        if annualized_volatility and not np.isnan(annualized_volatility)
        else np.nan
    )
    drawdown = calculate_drawdown(equity)
    return {
        "total_return": total_return,
        "ending_capital": equity.iloc[-1],
        "pnl": equity.iloc[-1] - initial_capital,
        "annualized_return": annualized_return,
        "annualized_volatility": annualized_volatility,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": drawdown.min(),
    }


def leveraged_returns(returns: pd.Series, leverage: float) -> pd.Series:
    return returns.fillna(0) * leverage


def calculate_full_period_vol_match_leverage(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:
    aligned = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()
    benchmark_vol = aligned["benchmark"].std()
    if benchmark_vol == 0 or np.isnan(benchmark_vol):
        return np.nan
    return aligned["strategy"].std() / benchmark_vol


def vol_matched_returns(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> tuple[pd.Series, float]:
    leverage = calculate_full_period_vol_match_leverage(strategy_returns, benchmark_returns)
    return leveraged_returns(benchmark_returns, leverage), leverage


def expanding_prior_vol_matched_returns(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    min_periods: int = TRADING_DAYS_PER_YEAR,
) -> pd.Series:
    aligned = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()
    strategy_vol = aligned["strategy"].expanding(min_periods=min_periods).std().shift(1)
    benchmark_vol = aligned["benchmark"].expanding(min_periods=min_periods).std().shift(1)
    leverage = strategy_vol / benchmark_vol
    leverage = leverage.replace([np.inf, -np.inf], np.nan).fillna(1.0)
    return aligned["benchmark"] * leverage


def beta_alpha_regression(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> dict:
    aligned = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()
    if len(aligned) < 2:
        return {
            "beta": np.nan,
            "daily_alpha": np.nan,
            "annualized_alpha_arithmetic": np.nan,
            "correlation": np.nan,
            "r_squared": np.nan,
        }

    x = aligned["benchmark"]
    y = aligned["strategy"]
    variance = x.var()
    beta = y.cov(x) / variance if variance != 0 else np.nan
    daily_alpha = y.mean() - beta * x.mean() if not np.isnan(beta) else np.nan
    correlation = y.corr(x)
    r_squared = correlation**2 if not np.isnan(correlation) else np.nan
    return {
        "beta": beta,
        "daily_alpha": daily_alpha,
        "annualized_alpha_arithmetic": daily_alpha * TRADING_DAYS_PER_YEAR,
        "correlation": correlation,
        "r_squared": r_squared,
    }


def upside_downside_capture(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> dict:
    aligned = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()
    up = aligned[aligned["benchmark"] > 0]
    down = aligned[aligned["benchmark"] < 0]

    avg_strategy_up = up["strategy"].mean() if not up.empty else np.nan
    avg_benchmark_up = up["benchmark"].mean() if not up.empty else np.nan
    avg_strategy_down = down["strategy"].mean() if not down.empty else np.nan
    avg_benchmark_down = down["benchmark"].mean() if not down.empty else np.nan

    upside_capture = (
        avg_strategy_up / avg_benchmark_up
        if avg_benchmark_up and not np.isnan(avg_benchmark_up)
        else np.nan
    )
    downside_capture = (
        avg_strategy_down / avg_benchmark_down
        if avg_benchmark_down and not np.isnan(avg_benchmark_down)
        else np.nan
    )
    return {
        "upside_capture": upside_capture,
        "downside_capture": downside_capture,
        "avg_strategy_return_on_spy_up_days": avg_strategy_up,
        "avg_strategy_return_on_spy_down_days": avg_strategy_down,
        "avg_spy_return_on_up_days": avg_benchmark_up,
        "avg_spy_return_on_down_days": avg_benchmark_down,
        "spy_up_days": len(up),
        "spy_down_days": len(down),
    }


def remove_years(returns: pd.Series, years: list[int]) -> pd.Series:
    returns = returns.copy()
    returns.index = pd.to_datetime(returns.index)
    return returns[~returns.index.year.isin(years)]


def worst_drawdown_period(equity: pd.Series) -> dict:
    equity = equity.dropna()
    drawdown = calculate_drawdown(equity)
    trough_date = drawdown.idxmin()
    peak_date = equity.loc[:trough_date].idxmax()
    recovered = equity.loc[trough_date:][equity.loc[trough_date:] >= equity.loc[peak_date]]
    recovery_date = recovered.index[0] if not recovered.empty else pd.NaT
    return {
        "drawdown_peak_date": peak_date,
        "drawdown_trough_date": trough_date,
        "drawdown_recovery_date": recovery_date,
        "max_drawdown": drawdown.loc[trough_date],
    }
