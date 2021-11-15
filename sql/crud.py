from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password
    db_user = models.User(first_name=user.first_name, name=user.name, username=user.username,
                          hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, username: str):
    db_user = db.query(models.User).filter(models.User.username == username).one()
    tmp = db.delete(db_user)
    db.commit()
    return tmp


def create_user_parameters(db: Session, parameters: schemas.ParametersCreate):
    db_parameters = models.Parameters(**parameters.dict())
    db.add(db_parameters)
    db.commit()
    db.refresh(db_parameters)
    return db_parameters


def get_parameters(db: Session, user_id: int):
    return db.query(models.Parameters).filter(models.Parameters.user_id == user_id).all()


def get_one_parameters_set(db: Session, parameters_id: int):
    return db.query(models.Parameters).filter(models.Parameters.id == parameters_id).first()


def create_user_investments(db: Session, investment: schemas.InvestmentCreate):
    db_investment = models.Investment(**investment.dict())
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment


def get_investments(db: Session, user_id: int):
    tmp = db.query(models.Investment).join(models.Parameters) \
        .filter(models.Parameters.user_id == user_id).all()
    return tmp


def create_user_token(db: Session, token: schemas.Token):
    db_token = models.Token(**token.dict())
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_token(db: Session, token: str):
   return db.query(models.Token).filter(models.Token.token == token).one()

