import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from apscheduler.schedulers.background import BackgroundScheduler

from db import SessionLocal
from models import Underlying, Expiry, OptionRow, Alert
from upstox_client import fetch_option_chain_snapshot

FETCH_INTERVAL_MIN = int(os.getenv("FETCH_INTERVAL_MIN", "5"))

def upsert_option_chain(db: Session, symbol: str):
    snap = fetch_option_chain_snapshot(symbol)
    # ensure underlying + expiry
    underlying = db.execute(select(Underlying).where(Underlying.symbol == symbol)).scalar_one_or_none()
    if not underlying:
        underlying = Underlying(symbol=symbol)
        db.add(underlying)
        db.flush()

    expiry = db.execute(
        select(Expiry).where(Expiry.underlying_id == underlying.id, Expiry.expiry == snap["expiry"])
    ).scalar_one_or_none()
    if not expiry:
        expiry = Expiry(underlying_id=underlying.id, expiry=snap["expiry"])
        db.add(expiry)
        db.flush()

    # upsert rows
    for r in snap["rows"]:
        row = db.execute(
            select(OptionRow).where(
                OptionRow.expiry_id == expiry.id,
                OptionRow.strike_price == r["strike"],
                OptionRow.option_type == r["type"],
            )
        ).scalar_one_or_none()
        if not row:
            row = OptionRow(expiry_id=expiry.id, strike_price=r["strike"], option_type=r["type"])
            db.add(row)
        row.delta = r["delta"]; row.gamma = r["gamma"]; row.theta = r["theta"]; row.vega = r["vega"]; row.rho = r["rho"]
        row.iv = r["iv"]; row.ltp = r["ltp"]; row.oi = r["oi"]; row.change_in_oi = r["change_in_oi"]
    db.commit()
    return expiry.id

def _compare(cond: str, value, threshold) -> bool:
    if value is None: return False
    value = float(value); threshold = float(threshold)
    if cond == ">": return value > threshold
    if cond == "<": return value < threshold
    if cond == "=": return value == threshold
    if cond == ">=": return value >= threshold
    if cond == "<=": return value <= threshold
    return False

def evaluate_alerts(db: Session, expiry_id: int):
    # join alerts with chain rows for same strike/type
    alerts = db.execute(select(Alert).where(Alert.expiry_id == expiry_id, Alert.triggered == False)).scalars().all()
    if not alerts: return 0

    chain_rows = db.execute(select(OptionRow).where(OptionRow.expiry_id == expiry_id)).scalars().all()
    # index by (strike,type)
    idx = {(float(cr.strike_price), cr.option_type): cr for cr in chain_rows}

    hits = 0
    for a in alerts:
        key = (float(a.strike_price), a.option_type)
        cr = idx.get(key)
        if not cr: continue
        greek_val = getattr(cr, a.greek, None)
        if _compare(a.condition, greek_val, a.threshold):
            a.triggered = True
            a.triggered_at = datetime.utcnow()
            hits += 1
    if hits:
        db.commit()
    return hits

def run_cycle(symbols=("BANKNIFTY",)):
    db = SessionLocal()
    try:
        for sym in symbols:
            expiry_id = upsert_option_chain(db, sym)
            evaluate_alerts(db, expiry_id)
    finally:
        db.close()

scheduler = BackgroundScheduler()
def start_scheduler():
    scheduler.add_job(run_cycle, "interval", minutes=FETCH_INTERVAL_MIN, id="fetch_cycle", replace_existing=True)
    scheduler.start()
