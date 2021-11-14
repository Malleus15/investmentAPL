from typing import List
import uvicorn

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from sql import crud, models, schemas
from sql.database import SessionLocal, engine

from business_logic import investment as invst

from fastapi.security import HTTPBasic
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import utils

# to eliminate all tables in db
# models.Base.metadata.drop_all(bind=engine)
# here we create all the tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
security = HTTPBasic()

current_user = ""


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


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)

    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/parameters/", response_model=schemas.Parameters)
def create_investment_for_user(parameters: schemas.ParametersCreate, db: Session = Depends(get_db)):
    check = invst.check_parameters(parameters.investors_number,
                                   parameters.number_rt_players,
                                   parameters.price_cpu,
                                   parameters.duration_cpu,
                                   parameters.hosting_capacity)
    if not check:
        raise HTTPException(status_code=400, detail="Bad request: some values in parameters are not allowed")
    return crud.create_user_parameters(db=db, parameters=parameters)


@app.get("/parameters/{user_id}", response_model=List[schemas.Parameters])
def read_parameters(user_id: int, db: Session = Depends(get_db)):
    parameters = crud.get_parameters(db, user_id=user_id)

    return parameters


# calcola tutte le grandezze relative all'intera coalizione
@app.post("/users/investment/", response_model=schemas.Investment)
async def create_investment_for_user(
        investment_req: schemas.InvestmentReqBase, db: Session = Depends(get_db)
):
    # firstly we find the parameters to use
    db_params = crud.get_one_parameters_set(db, parameters_id=investment_req.parameters_id)
    print(db_params)
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


@app.get("/investments/{user_id}", response_model=List[schemas.Investment])
def read_investments(user_id: int, db: Session = Depends(get_db)):
    investments = crud.get_investments(db, user_id=user_id)
    return investments


#################################
# authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(db, username: str):
    db_user = crud.get_user_by_username(db, username=username)
    if db_user:
        return db_user


def fake_decode_token(db, token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(db, token)
    return user


async def get_current_user(db, token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not form_data.password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = utils.get_random_string(length=160)
    tkn = schemas.TokenBase(token=token, user_id=user.id)
    crud.create_user_token(db, tkn)
    return {"access_token": token, "token_type": "bearer"}


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
