from datetime import datetime
from typing import List
import uvicorn

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from sqlalchemy.orm import Session

from sql import crud, models, schemas
from sql.database import SessionLocal, engine

from business_logic import investment as invst

from fastapi.security import HTTPBasic

import utils

# to eliminate all tables in db
#models.Base.metadata.drop_all(bind=engine)
# here we create all the tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
security = HTTPBasic()


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)

    try:

        request.state.db = SessionLocal()

        response = await call_next(request)

    finally:

        request.state.db.close()

    return response


# Dependency
def get_db(request: Request):
    return request.state.db


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.post("/users/delete/{token}")
def delete_usr(token: str, log_in: schemas.Login, db: Session = Depends(get_db)):
    if not crud.get_token(db, token):
        raise HTTPException(status_code=400, detail="Token expired redo the login!")

    db_user = crud.delete_user(db, username=log_in.username)
    if db_user is None:
        raise HTTPException(status_code=200, detail="OK")

    else:
        raise HTTPException(status_code=400, detail="User not found!")


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)

    return users


@app.get("/users/{username}", response_model=schemas.User)
def read_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/parameters/{token}", response_model=schemas.Parameters)
def create_parameters_for_user(token: str, parameters: schemas.ParametersCreate, db: Session = Depends(get_db)):
    if not crud.get_token(db, token):
        raise HTTPException(status_code=400, detail="Token expired redo the login!")
    check = invst.check_parameters(parameters.investors_number,
                                   parameters.number_rt_players,
                                   parameters.price_cpu,
                                   parameters.duration_cpu,
                                   parameters.hosting_capacity)
    if not check:
        raise HTTPException(status_code=400, detail="Bad request: some values in parameters are not allowed")
    return crud.create_user_parameters(db=db, parameters=parameters)


@app.get("/parameters/{user_id}/{token}", response_model=List[schemas.Parameters])
def read_parameters(user_id: int, token: str, db: Session = Depends(get_db)):
    if not crud.get_token(db, token):
        raise HTTPException(status_code=400, detail="Token expired redo the login!")
    parameters = crud.get_parameters(db, user_id=user_id)

    return parameters


@app.get("/parameters/delete/{params_id}/{token}")
def delete_params(params_id: int, token: str, db: Session = Depends(get_db)):
    if not crud.get_token(db, token):
        raise HTTPException(status_code=400, detail="Token expired redo the login!")

    db_parameters = crud.delete_params(db, params_id=params_id)
    if db_parameters is None:
        raise HTTPException(status_code=200, detail="OK")

    else:
        raise HTTPException(status_code=400, detail="Parameters not found!")


# calcola tutte le grandezze relative all'intera coalizione
@app.post("/users/investment/{token}", response_model=schemas.Investment)
async def create_investment_for_user(token: str,
        investment_req: schemas.InvestmentReqBase, db: Session = Depends(get_db)
):
    if not crud.get_token(db, token):
        raise HTTPException(status_code=400, detail="Token expired redo the login!")
    # firstly we find the parameters to use
    db_params = crud.get_one_parameters_set(db, parameters_id=investment_req.parameters_id)
    if db_params is None:
        raise HTTPException(status_code=404, detail="Parameters not found, parameters_id is wrong")
    # then we calculate the investment values
    # we don't pass directly the Parameters to reduce the dependency between packages
    (total_payoff, split_payoffs, split_revenues,
     split_payments) = invst.simulate_invest(db_params.investors_number,
                                             db_params.number_rt_players,
                                             db_params.price_cpu,
                                             db_params.hosting_capacity,
                                             db_params.duration_cpu,
                                             investment_req.fairness)
    # creating investment
    investment = schemas.InvestmentCreate(total_payoff=total_payoff,
                                          split_payments=str(split_payments),
                                          fairness=investment_req.fairness,
                                          split_revenues=str(split_revenues),
                                          split_payoffs=str(split_revenues),
                                          parameters_id=investment_req.parameters_id
                                          )

    return crud.create_user_investments(db=db, investment=investment)


@app.get("/investments/{user_id}/{token}", response_model=List[schemas.Investment])
def read_investments(user_id: int, token: str, db: Session = Depends(get_db)):
    if not crud.get_token(db, token):
        raise HTTPException(status_code=400, detail="Token expired redo the login!")

    investments = crud.get_investments(db, user_id=user_id)
    return investments


@app.get("/investments/delete/{invest_id}/{token}")
def delete_params(invest_id: int, token: str, db: Session = Depends(get_db)):
    if not crud.get_token(db, token):
        raise HTTPException(status_code=400, detail="Token expired redo the login!")

    db_investments = crud.delete_invest(db, invest_id=invest_id)
    if db_investments is None:
        raise HTTPException(status_code=200, detail="OK")

    else:
        raise HTTPException(status_code=400, detail="Parameters not found!")


#################################
# authentication
# Login
@app.post("/token")
async def login(log_in: schemas.Login, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username=log_in.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not log_in.password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = utils.get_random_string(length=160)
    tkn = schemas.TokenBase(token=token, user_id=user.id)
    crud.create_user_token(db, tkn)
    return {"access_token": token, "token_type": "bearer"}


def check_token(db: Session, token: str):
    tmp = crud.get_token(db, token)
    check = True
    c = datetime.now() - tmp.timestamp
    # convert to minutes
    c = c.seconds / 60
    # minute in which token is valid
    token_expiration = 120
    if c > token_expiration:
        check = False
    # check token expiration
    return check


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
