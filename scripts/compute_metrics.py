import pandas as pd
import numpy as np
from typing import Tuple, Dict
import statsmodels.api as sm

# =============================================================================
# Metric calculation utilities for mutual‑fund analysis
# =============================================================================

def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualised Sharpe ratio.

    Parameters
    ----------
    returns : pd.Series
        Daily returns expressed as decimal (e.g., 0.001 for 0.1%).
    risk_free_rate : float, optional
        Daily risk‑free rate (default 0). Must be on the same frequency as ``returns``.
    """
    excess = returns - risk_free_rate
    mean_excess = excess.mean()
    std_excess = excess.std(ddof=0)
    if std_excess == 0:
        return np.nan
    return np.sqrt(252) * mean_excess / std_excess


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualised Sortino ratio (downside‑risk version of Sharpe)."""
    excess = returns - risk_free_rate
    mean_excess = excess.mean()
    downside_std = excess[excess < 0].std(ddof=0)
    if downside_std == 0:
        return np.nan
    return np.sqrt(252) * mean_excess / downside_std


def beta_coefficient(returns: pd.Series, benchmark: pd.Series) -> float:
    """Beta of a fund relative to a benchmark index.

    Both series must be aligned on the same dates.
    """
    if len(returns) != len(benchmark):
        raise ValueError("Length mismatch between fund and benchmark returns")
    X = sm.add_constant(benchmark.values)
    model = sm.OLS(returns.values, X).fit()
    return float(model.params[1])


def alpha_annualized(returns: pd.Series, benchmark: pd.Series) -> float:
    """Annualised alpha (intercept) expressed in daily terms and scaled to yearly.
    """
    if len(returns) != len(benchmark):
        raise ValueError("Length mismatch between fund and benchmark returns")
    X = sm.add_constant(benchmark.values)
    model = sm.OLS(returns.values, X).fit()
    # Intercept is daily alpha; scale to yearly (252 trading days)
    return float(model.params[0] * 252)


def max_drawdown(nav_series: pd.Series) -> Tuple[float, str, str]:
    """Maximum drawdown and the dates of peak and trough.

    Returns
    -------
    max_dd : float
        The most negative drawdown (e.g., -0.25).
    peak_date : str
        Date (ISO string) of the peak preceding the max drawdown.
    trough_date : str
        Date (ISO string) of the trough.
    """
    running_max = nav_series.cummax()
    drawdown = nav_series / running_max - 1
    max_dd = drawdown.min()
    trough_date = drawdown.idxmin()
    peak_date = nav_series.loc[:trough_date].idxmax()
    return float(max_dd), str(peak_date.date()), str(trough_date.date())


def tracking_error(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Tracking error (annualised) between fund and benchmark returns."""
    diff = fund_returns - benchmark_returns
    return float(diff.std(ddof=0) * np.sqrt(252))


def var_cvar(returns: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
    """Value‑at‑Risk (VaR) and Conditional VaR (CVaR) for a given confidence level.

    Returns
    -------
    var : float
        The percentile loss (negative number).
    cvar : float
        Expected shortfall (average of losses beyond VaR).
    """
    var = returns.quantile(1 - confidence)
    cvar = returns[returns <= var].mean()
    return float(var), float(cvar)


def hhi(sector_weights: Dict[str, float]) -> float:
    """Herfindahl‑Hirschman Index for sector concentration.

    ``sector_weights`` maps sector name → weight (as a proportion, e.g., 0.25).
    """
    weights = np.array(list(sector_weights.values()))
    return float((weights ** 2).sum())


def cagr(start_value: float, end_value: float, years: float) -> float:
    """Compound Annual Growth Rate.

    Parameters
    ----------
    start_value, end_value : float
        NAV or portfolio value at the start and end of the period.
    years : float
        Length of the period in years.
    """
    if start_value <= 0 or years <= 0:
        return np.nan
    return (end_value / start_value) ** (1.0 / years) - 1


def cagr_multiple(nav_series: pd.Series) -> Tuple[float, float, float]:
    """Return CAGR for 1‑yr, 3‑yr and 5‑yr periods ending at the last date.

    The function assumes daily NAV with a ``date`` index.
    """
    end_date = nav_series.index.max()
    end_val = nav_series.loc[end_date]
    # 1‑year
    start_1y = end_date - pd.DateOffset(years=1)
    start_1y_val = nav_series.loc[start_1y] if start_1y in nav_series.index else np.nan
    cagr_1y = cagr(start_1y_val, end_val, 1) if not np.isnan(start_1y_val) else np.nan
    # 3‑year
    start_3y = end_date - pd.DateOffset(years=3)
    start_3y_val = nav_series.loc[start_3y] if start_3y in nav_series.index else np.nan
    cagr_3y = cagr(start_3y_val, end_val, 3) if not np.isnan(start_3y_val) else np.nan
    # 5‑year
    start_5y = end_date - pd.DateOffset(years=5)
    start_5y_val = nav_series.loc[start_5y] if start_5y in nav_series.index else np.nan
    cagr_5y = cagr(start_5y_val, end_val, 5) if not np.isnan(start_5y_val) else np.nan
    return float(cagr_1y), float(cagr_3y), float(cagr_5y)

# =============================================================================
# End of compute_metrics module
# =============================================================================

def run_monte_carlo(nav_series: pd.Series, years: int = 5, sims: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Monte‑Carlo simulation projecting NAV growth over a number of years.

    Parameters
    ----------
    nav_series : pd.Series
        Historical NAV indexed by date.
    years : int, optional
        Projection horizon in years (default 5).
    sims : int, optional
        Number of simulation paths (default 1000).
    seed : int, optional
        Random seed for reproducibility (default 42).

    Returns
    -------
    pd.DataFrame
        Columns ``simulation``, ``date`` and ``nav`` containing the simulated NAV paths.
    """
    np.random.seed(seed)
    # Daily returns from historical series
    daily_ret = nav_series.pct_change().dropna()
    mu = daily_ret.mean()
    sigma = daily_ret.std(ddof=0)
    steps = years * 252  # assuming 252 trading days per year
    # Generate business day dates after the last observed date
    start_date = nav_series.index[-1] + pd.DateOffset(days=1)
    dates = pd.date_range(start=start_date, periods=steps, freq='B')
    sims_data = []
    for sim in range(sims):
        # Simulate daily returns
        simulated_returns = np.random.normal(mu, sigma, steps)
        # Project NAV path
        nav_path = nav_series.iloc[-1] * np.cumprod(1 + simulated_returns)
        df = pd.DataFrame({
            'simulation': sim,
            'date': dates,
            'nav': nav_path
        })
        sims_data.append(df)
    return pd.concat(sims_data, ignore_index=True)

