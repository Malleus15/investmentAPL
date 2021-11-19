from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


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
    try:
        db_user = db.query(models.User).filter(models.User.username == username).first()
        db_token = db.query(models.Token).filter(models.Token.user_id == db_user.id).first()
        tmp = db.delete(db_user)
        db.delete(db_token)
        db.commit()
        return tmp
    except:
        tmp = ""
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


def delete_params(db: Session, params_id: int):
    try:
        db_params = db.query(models.Parameters).filter(models.Parameters.id == params_id).first()
        tmp = db.delete(db_params)
        db.delete(db_params)
        db.commit()
        return tmp
    except:
        tmp = ""
        return tmp


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


def delete_invest(db: Session, invest_id: int):
    try:
        db_invest = db.query(models.Investment).filter(models.Investment.id == invest_id).first()
        tmp = db.delete(db_invest)
        db.delete(db_invest)
        db.commit()
        return tmp
    except:
        tmp = ""
        return tmp


def create_user_token(db: Session, token: schemas.Token):
    db_token = models.Token(**token.dict())
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def get_token(db: Session, token: str):
    return db.query(models.Token).filter(models.Token.token == token).one()
