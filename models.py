from sqlalchemy import Column, Integer, String, Date, Numeric, Boolean, ForeignKey, DateTime, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    alerts = relationship("Alert", back_populates="user", cascade="all,delete")

class Underlying(Base):
    __tablename__ = "underlyings"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), unique=True, nullable=False)

    expiries = relationship("Expiry", back_populates="underlying", cascade="all,delete")

class Expiry(Base):
    __tablename__ = "expiries"
    id = Column(Integer, primary_key=True)
    underlying_id = Column(Integer, ForeignKey("underlyings.id", ondelete="CASCADE"))
    expiry = Column(Date, nullable=False)
    __table_args__ = (UniqueConstraint("underlying_id", "expiry", name="uq_underlying_expiry"),)

    underlying = relationship("Underlying", back_populates="expiries")
    option_rows = relationship("OptionRow", back_populates="expiry", cascade="all,delete")
    alerts = relationship("Alert", back_populates="expiry", cascade="all,delete")

class OptionRow(Base):
    __tablename__ = "option_chain"
    id = Column(Integer, primary_key=True)
    expiry_id = Column(Integer, ForeignKey("expiries.id", ondelete="CASCADE"), nullable=False)
    strike_price = Column(Numeric, nullable=False)
    option_type = Column(String(2), nullable=False)  # CE/PE
    delta = Column(Numeric)
    gamma = Column(Numeric)
    theta = Column(Numeric)
    vega = Column(Numeric)
    rho = Column(Numeric)
    iv = Column(Numeric)
    ltp = Column(Numeric)
    oi = Column(Numeric)
    change_in_oi = Column(Numeric)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        CheckConstraint("option_type IN ('CE','PE')", name="ck_option_type"),
        UniqueConstraint("expiry_id", "strike_price", "option_type", name="uq_chain_row"),
    )

    expiry = relationship("Expiry", back_populates="option_rows")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expiry_id = Column(Integer, ForeignKey("expiries.id", ondelete="CASCADE"), nullable=False)
    strike_price = Column(Numeric, nullable=False)
    option_type = Column(String(2), nullable=False)  # CE/PE
    greek = Column(String(10), nullable=False)       # delta/gamma/theta/vega/rho
    condition = Column(String(5), nullable=False)    # > < = >= <=
    threshold = Column(Numeric, nullable=False)
    triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint("option_type IN ('CE','PE')", name="ck_alert_option_type"),
        CheckConstraint("greek IN ('delta','gamma','theta','vega','rho')", name="ck_alert_greek"),
        CheckConstraint("condition IN ('>','<','=','>=','<=')", name="ck_alert_condition"),
    )

    user = relationship("User", back_populates="alerts")
    expiry = relationship("Expiry", back_populates="alerts")
