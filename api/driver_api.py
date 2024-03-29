from fastapi import HTTPException, Form, APIRouter
from jose import jwt
from decimal import Decimal
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import sqlite3

driverRouter = APIRouter()
# Connect to SQLite database
conn = sqlite3.connect('onionlk.db')
cursor = conn.cursor()

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

    # Execute SQL query to find the driver by mobileNumber
    cursor.execute("SELECT * FROM drivers WHERE mobileNumber=?", (mobileNumber.lstrip("0"),))
    driver = cursor.fetchone()

    # Check if driver exists and credentials are correct
    if driver and password == driver[2]:  # Assuming password is in the third column (index 2)
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
    mobileNumber: str = Form(...),
    locationLat: Decimal = Form(...),
    locationLng: Decimal = Form(...)
):
    # remove first char if it is 0
    if len(mobileNumber) == 10:
        mobileNumber = mobileNumber[1:]
    
    # Execute SQL query to find the driver by mobileNumber
    cursor.execute("SELECT * FROM drivers WHERE mobileNumber=?", (mobileNumber,))
    existing_driver = cursor.fetchone()

    if existing_driver:
        # Update the location of the driver
        new_location = {"locationLat": float(locationLat), "locationLng": float(locationLng)}
        cursor.execute("UPDATE drivers SET locationLat=?, locationLng=? WHERE mobileNumber=?", (new_location["locationLat"], new_location["locationLng"], mobileNumber))
        conn.commit()

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
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    print(f'lat1 : {lat1} lng1 : {lon1}')
    print(f'lat2 : {lat2} lng2 : {lon2}')

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c  # Radius of the Earth in kilometers
    print(f'distance : {distance}')

    return distance

# Endpoint to get nearby orders for a driver
@driverRouter.get("/driver/nearby_orders")
async def get_nearby_orders(
    mobileNumber: str,
    radius: float = 15  # Default radius in kilometers
):
    # remove first char if it is 0
    if len(mobileNumber) == 10:
        mobileNumber = mobileNumber[1:]

    # Connect to SQLite database
    conn = sqlite3.connect('onionlk.db')
    cursor = conn.cursor()

    # Find the driver by mobileNumber
    query = "SELECT * FROM drivers WHERE mobileNumber = ?"
    cursor.execute(query, (mobileNumber,))
    driver = cursor.fetchone()

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Driver not found",
        )

    # Get the driver's current location
    driver_location = {"lat": float(driver[3]), "lng": float(driver[4])}

    # Find nearby orders within the specified radius
    query = "SELECT * FROM orders"
    cursor.execute(query)
    nearby_orders = []

    for order in cursor.fetchall():
        order_location = {"lat": float(order[6]), "lng": float(order[7])}
        print(f'order_location : {order_location}')
        print(f'driver_location : {driver_location}')
        distance = calculate_distance(
            driver_location["lat"], driver_location["lng"], order_location["lat"], order_location["lng"]
        )
        if distance <= radius:
            # Convert the order data to a dictionary
            order_dict = {
                "id": str(order[0]), 
                "imageUrl": order[1],  
                "description": order[2], 
                "userMobileNumber": order[3], 
                "storeName": order[4], 
                "maxBudget": float(order[5]), 
                "locationLat": float(order[6]), 
                "locationLng": float(order[7]), 
                "assignedDriverMobileNumber": (order[8]), 
                "orderStatus": order[9], 
                "review": order[10], 
                "reviewScore": order[11], 
            }
            nearby_orders.append(order_dict)

    # Close the database connection
    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": 'Successfully fetched nearby orders!',
        "body": nearby_orders
    }


@driverRouter.post("/driver/accept_order")
async def accept_order(
    mobileNumber: str,
    orderId: str,
):
    # remove first char if it is 0
    if len(mobileNumber) == 10:
        mobileNumber = mobileNumber[1:]
    
    # Connect to SQLite database
    conn = sqlite3.connect('onionlk.db')
    cursor = conn.cursor()

    # Find the order by id
    query = "SELECT * FROM orders WHERE orderId = ?"
    cursor.execute(query, (orderId,))
    existing_order = cursor.fetchone()

    if existing_order:
        # Update the order status
        updated_data = {"assignedDriverMobileNumber": mobileNumber, "orderStatus": 'Ongoing'}
        update_query = "UPDATE orders SET assignedDriverMobileNumber = ?, orderStatus = ? WHERE orderId = ?"
        cursor.execute(update_query, (mobileNumber, 'Ongoing', orderId))
        conn.commit()

        # Close the database connection
        cursor.close()
        conn.close()

        return {
            "success": True,
            "message": "Order accepted!",
        }
    else:
        # Close the database connection
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": f"Order with id {orderId} not found!",
        }


@driverRouter.post("/driver/complete_order")
async def complete_order(
    orderId: str,
):
    # Connect to SQLite database
    conn = sqlite3.connect('onionlk.db')
    cursor = conn.cursor()

    # Find the order by id
    query = "SELECT * FROM orders WHERE orderId = ?"
    cursor.execute(query, (orderId,))
    existing_order = cursor.fetchone()

    if existing_order:
        # Update the order status
        update_query = "UPDATE orders SET orderStatus = ? WHERE orderId = ?"
        cursor.execute(update_query, ('Completed', orderId))
        conn.commit()

        # Close the database connection
        cursor.close()
        conn.close()

        return {
            "success": True,
            "message": "Order completed!",
        }
    else:
        # Close the database connection
        cursor.close()
        conn.close()

        return {
            "success": False,
            "message": f"Order with id {orderId} not found!",
        }

