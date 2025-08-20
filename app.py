#main Flask app(only HTTP routes no BG Jobs)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)

class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    symbol = db.Column(db.String(50))
    expiry = db.Column(db.Date)
    strike_price = db.Column(db.Numeric)
    option_type = db.Column(db.String(10))
    greek = db.Column(db.String(10))
    condition = db.Column(db.String(5))  # >, <, >=, <=, ==
    threshold = db.Column(db.Numeric)
    triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime)

# --- ROUTES ---
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    hashed_pw = generate_password_hash(data["password"])
    user = User(username=data["username"], email=data["email"], password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created"}), 201

@app.route("/alerts", methods=["POST"])
def create_alert():
    data = request.json
    alert = Alert(**data)
    db.session.add(alert)
    db.session.commit()
    return jsonify({"message": "Alert created"}), 201

@app.route("/alerts", methods=["GET"])
def list_alerts():
    alerts = Alert.query.all()
    return jsonify([{
        "id": a.id,
        "symbol": a.symbol,
        "expiry": str(a.expiry),
        "strike_price": float(a.strike_price),
        "option_type": a.option_type,
        "greek": a.greek,
        "condition": a.condition,
        "threshold": float(a.threshold),
        "triggered": a.triggered
    } for a in alerts])

if __name__ == "__main__":
    app.run(debug=True)
