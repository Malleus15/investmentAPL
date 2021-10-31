from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship, backref

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    parameters = relationship("Parameters", back_populates="user")


class Parameters(Base):
    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True, index=True)

    investors_number = Column(Integer, index=True)
    investors_type_array = Column(String, index=True)
    price_cpu = Column(Float, index=True)
    hosting_capacity = Column(Integer, index=True)
    # years
    duration_cpu = Column(Integer, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="parameters")


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)

    total_payoff = Column(Float, index=True)
    split_payoffs = Column(String, index=True)
    split_revenues = Column(String, index=True)
    split_payments = Column(String, index=True)
    fairness = Column(Boolean, index=True)
    parameters_id = Column(Integer, ForeignKey('parameters.id'))

    parameters = relationship("Parameters", backref=backref("investments", uselist=False))
