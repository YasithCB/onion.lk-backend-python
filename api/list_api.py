from fastapi import APIRouter, File, UploadFile, Form
from decimal import Decimal
from gridfs import GridFS

from db import get_mongo_db
from models import Order

listRouter = APIRouter()
db = get_mongo_db()
fs = GridFS(db)

@listRouter.post("/listUpload")
async def create_order(
    listImage: UploadFile = File(...),
    userMobileNumber : str = Form(...),
    description: str = Form(...),
    maxBudget: Decimal = Form(...),
    storeName: str = Form(...),
    locationLat : Decimal = Form(...),
    locationLng : Decimal = Form(...)
):
    
    # Insert data into the "order" collection
    order_data = {
        "description": description,
        "userMobileNumber": userMobileNumber,
        "storeName": storeName,
        "maxBudget": float(maxBudget),
        "locationLat": float(locationLat),
        "locationLng": float(locationLng),
        "assignedDriverMobileNumber" : 'N/A',
        "orderStatus" : 'Pending',
    }
    
    # Read the image file content
    image_content = await listImage.read()
    # Save the image file to GridFS
    image_id = fs.put(image_content, filename=listImage.filename)
    # Add the image_id to the order_data
    order_data["listImage"] = str(image_id)

    # Assuming you have a collection named "order" in your database
    order_collection = db.order
    result = order_collection.insert_one(order_data)

    # Get the inserted record's ObjectId
    inserted_id = result.inserted_id

    # Return the inserted record's ObjectId
    return {
        "success": "true",
        "message": "The list upload was successful!",
        "inserted_id": str(inserted_id),
    }
