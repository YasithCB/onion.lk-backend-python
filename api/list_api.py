from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from decimal import Decimal
from gridfs import GridFS
from typing import Optional
from bson import ObjectId
import io
import boto3
from botocore.exceptions import NoCredentialsError

from db import get_mongo_db

listRouter = APIRouter()
db = get_mongo_db()
fs = GridFS(db)

def upload_to_aws(file, bucket, s3_file, acl="public-read"):
    print(f"Uploading {s3_file} to {bucket}")

    s3 = boto3.client('s3', aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                      aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                      region_name=os.environ.get("REGION_NAME"))
    try:
        # Ensure the file cursor is at the beginning before uploading
        file.seek(0)
        s3.upload_fileobj(file, bucket, s3_file, ExtraArgs={'ACL': acl})
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False


@listRouter.post("/listUpload")
async def create_order(
    listImage: Optional[UploadFile] = File(None),
    userMobileNumber: str = Form(...),
    description: Optional[str] = Form(None),
    maxBudget: Optional[Decimal] = Form(None),
    storeName: Optional[str] = Form(None),
    locationLat: Decimal = Form(...),
    locationLng: Decimal = Form(...),
):
    
    
    # # Read the image file content if provided
    # if listImage is not None:
    #     image_content = await listImage.read()
    #     # Save the image file to GridFS
    #     image_id = fs.put(image_content, filename=listImage.filename)
    #     # Add the image_id to the order_data
    #     order_data["listImage"] = str(image_id)
    
    # image upload to S3
    

    # Insert data into the "order" collection
    order_data = {
        "description": description,
        "userMobileNumber": userMobileNumber,
        "storeName": storeName,
        "maxBudget": float(maxBudget) if maxBudget is not None else None,
        "locationLat": float(locationLat),
        "locationLng": float(locationLng),
        "assignedDriverMobileNumber" : 'N/A',
        "orderStatus" : 'Pending',
        "listImageUrl" : '',
    }

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
    
    
@listRouter.get("/user/my_orders")
async def get_orders_by_user(
    mobileNumber: str,
):
    # Find orders by userMobileNumber
    orders_collection = db.order
    
    # Use find to get a cursor and then iterate over it
    orders_cursor = orders_collection.find({"userMobileNumber": mobileNumber})
    
    # Convert cursor to list to get all matching orders
    orders_list = list(orders_cursor)
    
    # Convert ObjectId to string for each order in the list
    for order in orders_list:
        order["_id"] = str(order["_id"])

    return {
        "success": True,
        "message": f'Orders of {mobileNumber} are successfully fetched!',
        "body": orders_list,
    }
   
    
@listRouter.get("/order/get_img")
async def get_order_image(image_id: str,):
    print('method running :::::::')

    # Convert the image_id to ObjectId
    image_id = ObjectId(image_id)

    # Retrieve the image content from GridFS
    image_content = fs.get(image_id).read()

    # Create a StreamingResponse to send the image as a response
    return StreamingResponse(io.BytesIO(image_content), media_type="image/jpeg")

