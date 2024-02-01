from fastapi import HTTPException, Form, APIRouter
from jose import JWTError, jwt
from decimal import Decimal
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

from db import get_mongo_db

driverRouter = APIRouter()
db = get_mongo_db()

# Function to create JWT token
def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "your-secret-key", algorithm="HS256")
    return encoded_jwt

@driverRouter.post("/driver/auth")
async def driver_auth(
    mobileNumber: str = Form(...),
    password: str = Form(...),
):

    # Assuming you have a collection named "drivers" in your database
    drivers_collection = db.drivers

    # Find the driver by mobileNumber
    query = {"mobileNumber": mobileNumber}
    driver = drivers_collection.find_one(query)

    # Check if driver exists and credentials are correct
    if driver and password == driver["password"]:
        token_data = {"sub": mobileNumber}
        return {'success': 'true', "access_token": create_jwt_token(token_data), "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    
@driverRouter.post("/driver/update_location")
async def update_driver_location(
    mobileNumber : str = Form(...),
    locationLat : Decimal = Form(...),
    locationLng : Decimal = Form(...)
):
    # Assuming you have a collection named "drivers" in your database
    drivers_collection = db.drivers

    # Find the driver by mobileNumber
    query = {"mobileNumber": mobileNumber}
    existing_driver = drivers_collection.find_one(query)

    if existing_driver:
        # Update the location of the driver
        new_location = {"locationLat": float(locationLat), "locationLng": float(locationLng)}
        drivers_collection.update_one(query, {"$set": new_location})

        return {
            "success": "true",
            "message": f"Location updated for driver with mobile number {mobileNumber}!",
        }
    else:
        return {
            "success": "false",
            "message": f"Driver with mobile number {mobileNumber} not found!",
        }
        
    
# Function to calculate distance between two coordinates using Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) * sin(dlat / 2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) * sin(dlon / 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c  # Distance in kilometers
        
    return distance
    
# Endpoint to get nearby orders for a driver
@driverRouter.get("/driver/nearby_orders")
async def get_nearby_orders(
    mobileNumber: str,
    radius: float = 15  # Default radius in kilometers
):
    
    # Find the driver by mobileNumber
    drivers_collection = db.drivers
    query = {"mobileNumber": mobileNumber}
    driver = drivers_collection.find_one(query)
    
    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver not found",
        )

    # Get the driver's current location
    driver_location = {"lat": driver["locationLat"], "lng": driver["locationLng"]}

    # Find nearby orders within the specified radius
    orders_collection = db.order
    nearby_orders = []

    for order in orders_collection.find():
        order_location = {"lat": order["locationLat"], "lng": order["locationLng"]}
        distance = calculate_distance(
            driver_location["lat"], driver_location["lng"], order_location["lat"], order_location["lng"]
        )
        if distance <= radius:
            # Convert ObjectId to string
            order["_id"] = str(order["_id"])
            nearby_orders.append(order)

    return {"nearby_orders": nearby_orders}



@driverRouter.post("/driver/accept_order")
async def accept_order(
    mobileNumber : str = Form(...),
    orderId : str = Form(...),
    
):
    # Assuming you have a collection named "drivers" in your database
    orders_collection = db.order

    # Find the order by id
    query = {"_id": orderId}
    existing_order = orders_collection.find_one(query)

    if existing_order:
        # Update the location of the driver
        updated_data = {"assignedDriverMobileNumber": mobileNumber, "orderStatus": 'Ongoing'}
        orders_collection.update_one(query, {"$set": updated_data})

        return {
            "success": "true",
            "message": "Order accepted Succeful!",
        }
    else:
        return {
            "success": "false",
            "message": f"Order with id {orderId} not found!",
        }
