from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import select
from db import SessionLocal
from models import Underlying, Expiry, OptionRow

bp_market = Blueprint("market", __name__)

@bp_market.route("/option_chain", methods=["GET"])
def get_chain():
    symbol = request.args.get("symbol")
    expiry = request.args.get("expiry")  # YYYY-MM-DD
    if not symbol or not expiry:
        return jsonify({"error": "symbol and expiry required"}), 400
    db: Session = SessionLocal()
    try:
        under = db.execute(select(Underlying).where(Underlying.symbol == symbol)).scalar_one_or_none()
        if not under: return jsonify([])
        exp = db.execute(select(Expiry).where(Expiry.underlying_id == under.id, Expiry.expiry == expiry)).scalar_one_or_none()
        if not exp: return jsonify([])
        rows = db.execute(select(OptionRow).where(OptionRow.expiry_id == exp.id)).scalars().all()
        out = []
        for r in rows:
            out.append({
                "strike": float(r.strike_price),
                "type": r.option_type,
                "delta": float(r.delta) if r.delta is not None else None,
                "gamma": float(r.gamma) if r.gamma is not None else None,
                "theta": float(r.theta) if r.theta is not None else None,
                "vega": float(r.vega) if r.vega is not None else None,
                "rho": float(r.rho) if r.rho is not None else None,
                "iv": float(r.iv) if r.iv is not None else None,
                "ltp": float(r.ltp) if r.ltp is not None else None,
                "oi": float(r.oi) if r.oi is not None else None,
                "change_in_oi": float(r.change_in_oi) if r.change_in_oi is not None else None,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None
            })
        return jsonify(out)
    finally:
        db.close()
