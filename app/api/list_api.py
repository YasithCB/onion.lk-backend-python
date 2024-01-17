from fastapi import APIRouter, File, UploadFile, Form

listRouter = APIRouter()

@listRouter.post("/listUpload")
async def create_upload_file(
    listImage: UploadFile = File(...),
    description: str = Form(...),
    storeName: str = Form(...),
):
    return {
        'message' : 'success',
        'content' : 'The list upload successfull!'
    }
