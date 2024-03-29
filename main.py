# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi.middleware.cors import CORSMiddleware
from api.list_api import listRouter
from api.driver_api import driverRouter
import sqlite3

import secrets

app = FastAPI()
# Assuming you have a SQLite database file named 'onionlk.db'
db_path = 'onionlk.db'

origins = [
    "http://localhost:4000",  # Replace with your frontend port
    "http://192.168.100.2:4000",  # Allow the FastAPI server to make requests to itself
    "http://localhost:4000",  # Allow the FastAPI server to make requests to itself
]

# Allow all origins, methods, and headers for simplicity (modify as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your API routes
app.include_router(listRouter)
app.include_router(driverRouter)

# Secret key to sign the JWT tokens (change this in a real application)
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"

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

@app.get("/")
def read_root():
    return {"message": "Welcome to Union.lk"}
  
# Dependency to get the current user based on the JWT token
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query the user based on the username (mobileNumber)
    cursor.execute("SELECT * FROM users WHERE mobileNumber=?", (username,))
    user = cursor.fetchone()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    if user is None:
        raise credentials_exception

    return user

# Route to get a token for authentication
@app.post("/user/auth")
async def create_token(form_data: dict):
    mobileNumber = form_data["mobileNumber"]
    password = form_data["password"]

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query the user by mobileNumber
    cursor.execute("SELECT * FROM users WHERE mobileNumber=?", (mobileNumber.lstrip("0"),))
    user = cursor.fetchone()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    # Check if user exists and credentials are correct
    if user and password == user[2]:  # Assuming password is at index 2
        token_data = {"sub": mobileNumber}
        return {
            'success': 'true',
            'message': "User authenticated!",
            "access_token": create_jwt_token(token_data),
            "token_type": "bearer",
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


