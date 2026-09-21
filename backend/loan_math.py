def compute_emi(amount: float, rate: float, tenure_years: float) -> dict:
    """EMI = P * r * (1+r)^n / ((1+r)^n - 1), r = monthly rate, n = months."""
    months = round(tenure_years * 12)
    monthly_rate = rate / 12 / 100

    if months <= 0:
        emi = 0.0
    elif monthly_rate == 0:
        emi = amount / months
    else:
        factor = (1 + monthly_rate) ** months
        emi = amount * monthly_rate * factor / (factor - 1)

    total_payment = emi * months
    total_interest = max(total_payment - amount, 0.0)

    return {
        "emi": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2),
    }
