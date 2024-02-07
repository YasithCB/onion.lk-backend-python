# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel,SecretStr
from fastapi.middleware.cors import CORSMiddleware

from api.list_api import listRouter
from api.driver_api import driverRouter
from db import get_mongo_db

import secrets

app = FastAPI()
# Get the MongoDB database object
db = get_mongo_db()

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

# Load the TrOCR model and processor
# processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
# model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')

# Include your API routes
app.include_router(listRouter)
app.include_router(driverRouter)

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

@app.get("/")
def read_root():
    return {"message": "Welcome to Union.lk"}

# @app.post("/predict")
# async def predict(file: UploadFile = File(...)):
#     # Read the uploaded image
#     contents = await file.read()
#     image = Image.open(io.BytesIO(contents)).convert("RGB")

#     # Preprocess the image using the TrOCR processor
#     pixel_values = processor(images=image, return_tensors="pt").pixel_values

#     # Generate text using the TrOCR model
#     generated_ids = model.generate(pixel_values)
#     generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

#     return {"text": generated_text}


# Route to get information about the current user
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Route to get a token for authentication
@app.post("/user/auth")
async def create_token(form_data: dict):
    mobileNumber = form_data["mobileNumber"]
    password = form_data["password"]
    
    # Assuming you have a collection named "users" in your database
    users_collection = db.users

    # Find the user by mobileNumber
    query = {"mobileNumber": mobileNumber}
    user = users_collection.find_one(query)

    # Check if user exists and credentials are correct
    if user and password == user["password"]:
        token_data = {"sub": mobileNumber}
        return {'success': 'true',
                'message' : "User authenticated!",
                "access_token": create_jwt_token(token_data),
                "token_type": "bearer",
                }
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


