from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy import select
from db import SessionLocal
from models import User, Alert, Expiry, Underlying
from auth import decode_token

bp_alerts = Blueprint("alerts", __name__)

def _require_user_id(req) -> int | None:
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "): return None
    token = auth.split(" ", 1)[1]
    return decode_token(token)

@bp_alerts.route("/alerts", methods=["GET"])
def list_alerts():
    user_id = _require_user_id(request)
    if not user_id: return jsonify({"error": "unauthorized"}), 401
    db: Session = SessionLocal()
    try:
        alerts = db.execute(select(Alert).where(Alert.user_id == user_id)).scalars().all()
        out = []
        for a in alerts:
            out.append({
                "id": a.id,
                "expiryId": a.expiry_id,
                "strike": float(a.strike_price),
                "type": a.option_type,
                "greek": a.greek,
                "condition": a.condition,
                "threshold": float(a.threshold),
                "triggered": a.triggered,
                "triggeredAt": a.triggered_at.isoformat() if a.triggered_at else None
            })
        return jsonify(out)
    finally:
        db.close()

@bp_alerts.route("/alerts", methods=["POST"])
def create_alert():
    user_id = _require_user_id(request)
    if not user_id: return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(force=True) or {}
    required = ["symbol", "expiry", "strike", "type", "greek", "condition", "threshold"]
    missing = [k for k in required if k not in data]
    if missing: return jsonify({"error": f"missing: {','.join(missing)}"}), 400

    db: Session = SessionLocal()
    try:
        # ensure underlying+expiry exist
        under = db.execute(select(Underlying).where(Underlying.symbol == data["symbol"])).scalar_one_or_none()
        if not under:
            from models import Underlying as U
            under = U(symbol=data["symbol"])
            db.add(under)
            db.flush()

        from models import Expiry as E
        exp = db.execute(select(E).where(E.underlying_id == under.id, E.expiry == data["expiry"])).scalar_one_or_none()
        if not exp:
            exp = E(underlying_id=under.id, expiry=data["expiry"])
            db.add(exp)
            db.flush()

        alert = Alert(
            user_id=user_id,
            expiry_id=exp.id,
            strike_price=data["strike"],
            option_type=data["type"],
            greek=data["greek"],
            condition=data["condition"],
            threshold=data["threshold"],
        )
        db.add(alert)
        db.commit()
        return jsonify({"id": alert.id}), 201
    finally:
        db.close()
