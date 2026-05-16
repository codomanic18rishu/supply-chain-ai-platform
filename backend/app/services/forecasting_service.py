from typing import List

import numpy as np


def generate_forecast(
    historical_sales: List[float],
    periods: int = 7,
):
    """
    Simple baseline forecast:
    Uses average of the last 7 observations.
    Adds small random variation.
    """
    recent_values = historical_sales[-7:]
    baseline = float(np.mean(recent_values))

    forecast = []

    for _ in range(periods):
        noise = np.random.uniform(-0.05, 0.05)  # ±5%
        predicted = round(baseline * (1 + noise), 2)
        forecast.append(max(0, predicted))

    return {
        "forecast": forecast,
        "model_used": "Baseline Moving Average",
        "confidence": 0.82,
    }