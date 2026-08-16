"""Calculs financiers deterministes utilises par les rapports metier."""

from datetime import date
from decimal import Decimal, InvalidOperation, localcontext


ZERO = Decimal("0")
ONE = Decimal("1")
DAYS_PER_YEAR = Decimal("365")


def xirr(cashflows: list[tuple[date, Decimal]]) -> Decimal:
    """Calcule un rendement annualise date (type TMA/XIRR) par dichotomie.

    Les montants sont signes du point de vue de l'investisseur : sortie
    negative a la souscription, encaissements positifs ensuite.
    """
    flows = [(when, Decimal(amount)) for when, amount in cashflows if amount]
    if len(flows) < 2 or not any(amount < ZERO for _, amount in flows) or not any(amount > ZERO for _, amount in flows):
        return ZERO
    start = min(when for when, _ in flows)

    def npv(rate: Decimal) -> Decimal:
        with localcontext() as context:
            context.prec = 34
            base = ONE + rate
            if base <= ZERO:
                return Decimal("Infinity")
            total = ZERO
            for when, amount in flows:
                years = Decimal((when - start).days) / DAYS_PER_YEAR
                discount = (base.ln() * years).exp()
                total += amount / discount
            return total

    with localcontext() as context:
        context.prec = 34
        low = Decimal("-0.9999")
        high = Decimal("10")
        low_value = npv(low)
        high_value = npv(high)
        while low_value * high_value > ZERO and high < Decimal("1000"):
            high *= Decimal("2")
            high_value = npv(high)
        if low_value * high_value > ZERO:
            return ZERO
        for _ in range(100):
            middle = (low + high) / Decimal("2")
            middle_value = npv(middle)
            if abs(middle_value) < Decimal("0.00000001"):
                return (middle * Decimal("100")).quantize(Decimal("0.01"))
            if low_value * middle_value <= ZERO:
                high, high_value = middle, middle_value
            else:
                low, low_value = middle, middle_value
        return (((low + high) / Decimal("2")) * Decimal("100")).quantize(Decimal("0.01"))


def annualized_return(invested: Decimal, current_value: Decimal, start: date, as_of: date, paid_interest: Decimal = ZERO, fee_amount: Decimal = ZERO) -> Decimal:
    """Retourne le TMA en pourcentage pour une position et ses flux connus."""
    if invested <= ZERO or as_of <= start:
        return ZERO
    return xirr([
        (start, -(Decimal(invested) + Decimal(fee_amount))),
        (as_of, Decimal(current_value) + Decimal(paid_interest)),
    ])

