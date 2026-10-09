from datetime import date
from app.services.risk import calculate_batch_risk

def test_batch_risk_simple_case():
    result = calculate_batch_risk(20, 12, date(2030, 1, 2), date(2030, 1, 1))
    assert result.at_risk_units == 8
    assert result.risk_percent == 40.0
    assert result.days_to_expiry == 1
