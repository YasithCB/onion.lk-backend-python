import sqlite3
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from decimal import Decimal
from typing import Optional
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import os
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import requests
import warnings

# Load environment variables from .env file
load_dotenv()

listRouter = APIRouter()
# Assuming you have a SQLite database file named "onionlk.db"
conn = sqlite3.connect('onionlk.db')
cursor = conn.cursor()

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

async def image_to_text(imageUrl):
    print('running model')
    # Suppress the specific warning
    warnings.filterwarnings("ignore", message="Some weights of VisionEncoderDecoderModel were not initialized")

    image = Image.open(requests.get(imageUrl, stream=True).raw).convert("RGB")

    processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
    model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')
    pixel_values = processor(images=image, return_tensors="pt").pixel_values

    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return generated_text

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
    # Check if listImage is provided
    if listImage is not None:
        # Upload the image to AWS S3
        bucket_name = 'onionlk'
        region_name = '.s3.ap-south-1.amazonaws.com'
        s3_file_path = f"uploads/{listImage.filename}"
        
        if not upload_to_aws(listImage.file, bucket_name, s3_file_path):
            # Handle the case when the upload fails
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")

        image_url = f"https://{bucket_name}{region_name}/{s3_file_path}"
        # generated_text = await image_to_text(image_url)
        # print(generated_text)
    else:
        image_url = None

    # Insert data into the "orders" table
    order_data = {
        "imageUrl": image_url,
        "description": description,
        "userMobileNumber": userMobileNumber,
        "storeName": storeName,
        "maxBudget": float(maxBudget) if maxBudget is not None else None,
        "locationLat": float(locationLat),
        "locationLng": float(locationLng),
        "assignedDriverMobileNumber": 'N/A',
        "orderStatus": 'Pending',
    }

    cursor.execute('''
        INSERT INTO orders (
            imageUrl,
            description,
            userMobileNumber,
            storeName,
            maxBudget,
            locationLat,
            locationLng,
            assignedDriverMobileNumber,
            orderStatus
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order_data["imageUrl"],
        order_data["description"],
        order_data["userMobileNumber"],
        order_data["storeName"],
        order_data["maxBudget"],
        order_data["locationLat"],
        order_data["locationLng"],
        order_data["assignedDriverMobileNumber"],
        order_data["orderStatus"],
    ))

    # Commit the changes
    conn.commit()

    # Get the inserted record's rowid
    inserted_id = cursor.lastrowid

    # Return the inserted record's rowid
    return {
        "success": "true",
        "message": "The list upload was successful!",
        "inserted_id": str(inserted_id),
    }

@listRouter.get("/user/my_orders")
async def get_orders_by_user(
    mobileNumber: str,
):
    # Execute SQL query to fetch orders by userMobileNumber
    cursor.execute("SELECT * FROM orders WHERE userMobileNumber=?", (mobileNumber,))
    orders = cursor.fetchall()

    # Convert ObjectId to string for each order in the list
    orders_list = [dict(zip([column[0] for column in cursor.description], order)) for order in orders]
    for order in orders_list:
        order["_id"] = str(order["_id"])

    return {
        "success": True,
        "message": f'Orders of {mobileNumber} are successfully fetched!',
        "body": orders_list,
    }

