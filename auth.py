import os, datetime, jwt
from werkzeug.security import generate_password_hash, check_password_hash

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "10080"))

def hash_password(pw: str) -> str:
    return generate_password_hash(pw)

def verify_password(hash_: str, pw: str) -> bool:
    return check_password_hash(hash_, pw)

def create_token(user_id: int) -> str:
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_MINUTES)
    payload = {"sub": user_id, "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except Exception:
        return None
