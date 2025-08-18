import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from db import Base, engine
from models import User
from auth import hash_password, verify_password, create_token
from routes_alerts import bp_alerts
from routes_market import bp_market
from scheduler import start_scheduler, run_cycle

from sqlalchemy import select
from db import SessionLocal

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)  # allow Android emulator/dev
    Base.metadata.create_all(bind=engine)

    @app.post("/register")
    def register():
        data = request.get_json(force=True) or {}
        for f in ("username","email","password"):
            if f not in data: return jsonify({"error": f"missing {f}"}), 400
        db = SessionLocal()
        try:
            # check unique
            if db.execute(select(User).where(User.username==data["username"])).scalar_one_or_none():
                return jsonify({"error":"username taken"}), 409
            if db.execute(select(User).where(User.email==data["email"])).scalar_one_or_none():
                return jsonify({"error":"email taken"}), 409

            u = User(username=data["username"], email=data["email"], password_hash=hash_password(data["password"]))
            db.add(u); db.commit()
            return jsonify({"status":"ok"}), 201
        finally:
            db.close()

    @app.post("/login")
    def login():
        data = request.get_json(force=True) or {}
        if "email" not in data or "password" not in data:
            return jsonify({"error":"missing credentials"}), 400
        db = SessionLocal()
        try:
            u = db.execute(select(User).where(User.email==data["email"])).scalar_one_or_none()
            if not u or not verify_password(u.password_hash, data["password"]):
                return jsonify({"error":"invalid credentials"}), 401
            token = create_token(u.id)
            return jsonify({"token": token, "userId": u.id})
        finally:
            db.close()

    # Blueprints
    app.register_blueprint(bp_alerts)
    app.register_blueprint(bp_market)

    # start first cycle immediately (fast feedback), then background scheduler
    @app.before_first_request
    def boot():
        # run a one-off cycle so DB has data
        try:
            run_cycle(symbols=("BANKNIFTY",))
        except Exception as e:
            print("Initial cycle failed:", e)
        start_scheduler()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
