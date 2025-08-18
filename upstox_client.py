import os
from datetime import date, datetime
from decimal import Decimal

# TODO: wire real Upstox calls per https://upstox.com/developer/api-documentation/option-greek
# For now, return a tiny fake snapshot for one underlying/expiry.

def fetch_option_chain_snapshot(symbol: str):
    """
    Return structure:
    {
      'expiry': date,
      'rows': [
        {'strike': 22000, 'type': 'CE', 'delta': 0.55, 'gamma': 0.01, ...},
        {'strike': 22000, 'type': 'PE', 'delta': -0.45, ...},
        ...
      ]
    }
    """
    # Stub: one expiry, 3 strikes
    exp = date.today()
    rows = []
    for k in [22000, 22100, 22200]:
        rows.append({'strike': k, 'type': 'CE', 'delta': Decimal("0.50"), 'gamma': Decimal("0.01"),
                     'theta': Decimal("-0.03"), 'vega': Decimal("0.12"), 'rho': Decimal("0.01"),
                     'iv': Decimal("0.15"), 'ltp': Decimal("120.5"), 'oi': Decimal("150000"), 'change_in_oi': Decimal("5000")})
        rows.append({'strike': k, 'type': 'PE', 'delta': Decimal("-0.50"), 'gamma': Decimal("0.01"),
                     'theta': Decimal("-0.03"), 'vega': Decimal("0.12"), 'rho': Decimal("-0.01"),
                     'iv': Decimal("0.16"), 'ltp': Decimal("110.2"), 'oi': Decimal("140000"), 'change_in_oi': Decimal("-3000")})
    return {"symbol": symbol, "expiry": exp, "rows": rows}
