# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel,SecretStr
from typing import Optional
from api.list_api import listRouter

import secrets

app = FastAPI()

# Include your API routes
app.include_router(listRouter)


# Secret key to sign the JWT tokens (change this in a real application)
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"

print(SECRET_KEY)

# Define your user model (replace this with your own user model)
class User(BaseModel):
    mobileNumber: str
    password: SecretStr

# Fake user data (replace this with your user authentication logic)
fake_users_db = {
    "user1": {
         "mobileNumber": "0767722095",
         "password": "123456",
    },
    "user2": {
         "mobileNumber": "0767722096",
         "password": "123456",
    },
}

# OAuth2PasswordBearer is a class for handling OAuth2-style bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Function to create a JWT token
def create_jwt_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# Function to decode a JWT token
def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Dependency to get the current user from the token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_jwt_token(token)
    if payload is None:
        raise credentials_exception
    return payload

# Route to get information about the current user
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Route to get a token for authentication
@app.post("/token")
async def create_token(form_data: dict):
    mobileNumber = form_data["mobileNumber"]
    password = form_data["password"]
    
    # find user on list
    user = None
    for user_key, user_data in fake_users_db.items():
        if user_data["mobileNumber"] == mobileNumber:
            user = user_data
            break

    # check if credentials correct
    if user is None or password != user["password"]:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token_data = {"sub": mobileNumber}
    return {'message' : 'success' ,"access_token": create_jwt_token(token_data), "token_type": "bearer"}


