from dataclasses import dataclass
from datetime import date

@dataclass
class BatchRisk:
    quantity: int
    forecast_demand_before_expiry: int
    at_risk_units: int
    risk_percent: float
    days_to_expiry: int

def calculate_batch_risk(quantity: int, forecast_demand_before_expiry: int, expiry_date: date, as_of: date | None = None) -> BatchRisk:
    """Transparent baseline heuristic; not a trained or calibrated model."""
    today = as_of or date.today()
    if quantity < 0 or forecast_demand_before_expiry < 0:
        raise ValueError("Quantities must be non-negative.")
    days = (expiry_date - today).days
    sellable_demand = min(quantity, forecast_demand_before_expiry) if days >= 0 else 0
    at_risk = max(0, quantity - sellable_demand)
    risk = (at_risk / quantity * 100) if quantity else 0.0
    return BatchRisk(quantity, forecast_demand_before_expiry, at_risk, round(risk, 1), days)
