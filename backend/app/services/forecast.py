import pandas as pd
from sklearn.metrics import mean_absolute_error

def moving_average_forecast(values: list[float], window: int = 7) -> dict:
    if not values:
        raise ValueError("At least one historical sales value is required.")
    if window < 1:
        raise ValueError("window must be at least 1.")
    series = pd.Series(values, dtype="float64").tail(window)
    return {"method":"moving_average_baseline","observations_used":int(series.count()),"forecast_units":round(float(series.mean()),2),"mae":None}

def evaluate_forecast(actual: list[float], predicted: list[float]) -> dict:
    if len(actual) != len(predicted) or not actual:
        raise ValueError("Actual and predicted must have equal, non-zero lengths.")
    return {"mae":round(float(mean_absolute_error(actual, predicted)),3),"n":len(actual)}
