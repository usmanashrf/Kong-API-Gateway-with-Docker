from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi import FastAPI
from sqlmodel import SQLModel
from typing import Optional
import jwt
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("read data services started")
    yield
    
app = FastAPI(lifespan = lifespan, title="read data services")

class TokenData(SQLModel):
    iss: str


SECRET_KEY = "zPcYqCVrd1UXG5OPVcNb8QylDwpopNOu"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600


def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = min(expire, datetime(2038, 1, 19, 3, 14, 7))  # Limit expiration time to 2038-01-19 03:14:07 UTC
    to_encode.update({"exp": expire})
    headers = {
        "typ": "JWT",
        "alg": ALGORITHM
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM, headers=headers)
    return encoded_jwt


@app.post("/generate-token/")
def generate_token(data: TokenData):
    payload = {"iss": data.iss}
    token = create_jwt_token(payload)
    return {"token": token}