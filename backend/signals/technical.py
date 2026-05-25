"""
Technical signal scoring: RSI, MACD, 50-day SMA.
Returns a float 0.0 - 1.0.
"""
import pandas as pd

try:
    import pandas_ta as ta
    USE_PANDAS_TA = True
except ImportError:
    USE_PANDAS_TA = False


def compute_technical_score(df: pd.DataFrame) -> float:
    """
    Compute technical score from OHLCV DataFrame.

    Components (sum to 1.0):
      - RSI recovery (0.40): RSI 14-period between 30-50 = recovering from oversold
      - MACD bullish  (0.35): MACD histogram positive / crossing above signal
      - Price > 50 MA (0.25): Current price above 50-day simple moving average
    """
    close = df["Close"]

    rsi_score = _score_rsi(close)
    macd_score = _score_macd(close)
    ma_score = _score_ma(close)

    return rsi_score * 0.40 + macd_score * 0.35 + ma_score * 0.25


def _score_rsi(close: pd.Series) -> float:
    """
    RSI scoring: ideal range 30-50 (recovering from oversold).

      RSI 30-50 -> 1.0
      RSI 20-30 -> linear 0.5 to 1.0
      RSI 50-70 -> linear 1.0 to 0.3
      RSI < 20  -> 0.3
      RSI > 70  -> 0.0
    """
    rsi_val = _compute_rsi(close)
    if rsi_val is None:
        return 0.0

    if 30 <= rsi_val <= 50:
        return 1.0
    elif 20 <= rsi_val < 30:
        return 0.5 + (rsi_val - 20) / 10 * 0.5
    elif 50 < rsi_val <= 70:
        return 1.0 - (rsi_val - 50) / 20 * 0.7
    elif rsi_val < 20:
        return 0.3
    else:
        return 0.0


def _score_macd(close: pd.Series) -> float:
    """
    MACD scoring: bullish crossover = histogram turning positive.

      Histogram positive and increasing -> 1.0
      Histogram just turned positive     -> 1.0
      Histogram positive but decreasing  -> 0.6
      Histogram negative but increasing  -> 0.4
      Histogram negative and decreasing  -> 0.0
    """
    _, _, histogram = _compute_macd(close)
    if histogram is None or len(histogram) < 2:
        return 0.0

    current_hist = histogram.iloc[-1]
    prev_hist = histogram.iloc[-2]

    if pd.isna(current_hist) or pd.isna(prev_hist):
        return 0.0

    if current_hist > 0:
        if prev_hist <= 0:
            return 1.0
        elif current_hist > prev_hist:
            return 1.0
        else:
            return 0.6
    else:
        if current_hist > prev_hist:
            return 0.4
        else:
            return 0.0


def _score_ma(close: pd.Series) -> float:
    """
    Price vs 50-day SMA scoring.

      Price > SMA by 0-5%  -> 1.0
      Price > SMA by 5%+   -> 0.7 decay toward 0.5
      Price < SMA by 0-5%  -> 0.5
      Price < SMA by 5%+   -> 0.2
    """
    sma = _compute_sma(close, length=50)
    if sma is None:
        return 0.0

    current_price = float(close.iloc[-1])
    pct_diff = (current_price - sma) / sma

    if 0 <= pct_diff <= 0.05:
        return 1.0
    elif pct_diff > 0.05:
        return max(0.5, 1.0 - (pct_diff - 0.05) / 0.10 * 0.3)
    elif -0.05 <= pct_diff < 0:
        return 0.5
    else:
        return 0.2


# --- Indicator computation (pandas-ta with manual fallback) ---

def _compute_rsi(close: pd.Series, length: int = 14) -> float | None:
    if USE_PANDAS_TA:
        try:
            rsi_series = ta.rsi(close, length=length)
            if rsi_series is not None and not rsi_series.empty:
                val = rsi_series.iloc[-1]
                return float(val) if pd.notna(val) else None
        except Exception:
            pass

    # Manual fallback
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=length).mean()

    if loss.iloc[-1] == 0:
        return 100.0

    rs = gain.iloc[-1] / loss.iloc[-1]
    return float(100 - (100 / (1 + rs)))


def _compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    if USE_PANDAS_TA:
        try:
            macd_df = ta.macd(close, fast=fast, slow=slow, signal=signal)
            if macd_df is not None and not macd_df.empty:
                macd_line = macd_df.iloc[:, 0]
                histogram = macd_df.iloc[:, 1]
                signal_line = macd_df.iloc[:, 2]
                return macd_line, signal_line, histogram
        except Exception:
            pass

    # Manual fallback
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def _compute_sma(close: pd.Series, length: int = 50) -> float | None:
    if USE_PANDAS_TA:
        try:
            sma_series = ta.sma(close, length=length)
            if sma_series is not None and not sma_series.empty:
                val = sma_series.iloc[-1]
                return float(val) if pd.notna(val) else None
        except Exception:
            pass

    # Manual fallback
    if len(close) < length:
        return None
    return float(close.rolling(window=length).mean().iloc[-1])
