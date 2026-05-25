"""
Volume spike signal: today's volume vs 20-day average.
Returns a float 0.0 - 1.0.
"""
import pandas as pd


def compute_volume_score(df: pd.DataFrame) -> float:
    """
    Score volume spike: today's volume relative to 20-day average.

      Volume ratio >= 3.0x   -> 1.0
      Volume ratio 2.0-3.0x  -> 0.8 to 1.0
      Volume ratio 1.5-2.0x  -> 0.4 to 0.8
      Volume ratio 1.0-1.5x  -> 0.0 to 0.4
      Volume ratio < 1.0x    -> 0.0
    """
    if "Volume" not in df.columns or len(df) < 21:
        return 0.0

    volume = df["Volume"]
    today_vol = volume.iloc[-1]
    avg_20d = volume.iloc[-21:-1].mean()

    if avg_20d == 0 or pd.isna(avg_20d) or pd.isna(today_vol):
        return 0.0

    ratio = float(today_vol) / float(avg_20d)

    if ratio >= 3.0:
        return 1.0
    elif ratio >= 2.0:
        return 0.8 + (ratio - 2.0) / 1.0 * 0.2
    elif ratio >= 1.5:
        return 0.4 + (ratio - 1.5) / 0.5 * 0.4
    elif ratio >= 1.0:
        return (ratio - 1.0) / 0.5 * 0.4
    else:
        return 0.0
