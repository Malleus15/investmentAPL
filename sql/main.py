from typing import List
import uvicorn

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from sqlalchemy.orm import Session

from sql import crud, models, schemas
from sql.database import SessionLocal, engine

from business_logic import investment as invst

# to eliminate all tables in db
# models.Base.metadata.drop_all(bind=engine)
# here we create all the tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


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
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
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
def create_investment_for_user(
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
    # cannot use it like a normal constructor
    investment = schemas.InvestmentCreate(total_payoff=total_payoff,
                                          split_payments=str(split_payments),
                                          fairness=investment_req.fairness,
                                          split_revenues=str(split_revenues),
                                          split_payoffs=str(split_revenues),
                                          parameters_id=investment_req.parameters_id
                                          )

    return crud.create_user_investments(db=db, investment=investment)


@app.get("/investments/", response_model=List[schemas.Investment])
def read_investments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    investments = crud.get_investments(db, skip=skip, limit=limit)
    return investments


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
