from fastapi import APIRouter, File, UploadFile, Form
from decimal import Decimal

listRouter = APIRouter()

@listRouter.post("/listUpload/store")
async def create_order_with_store(
    listImage: UploadFile = File(...),
    description: str = Form(...),
    storeName: str = Form(...),
    maxBudget: Decimal = Form(...),
):
    return {
        'message' : 'success',
        'content' : f'The list upload successfull from {storeName}!'
    }

@listRouter.post("/listUpload")
async def create_order(
    listImage: UploadFile = File(...),
    description: str = Form(...),
    maxBudget: Decimal = Form(...),
):
    return {
        'message' : 'success',
        'content' : 'The list upload successfull!'
    }
