def create_place(db: Session, place: PlaceCreate, img: UploadFile):
    try:
        # Upload the image to AWS S3
        bucket_name = 'travel-app-images'
        region_name = '.s3.ap-south-1.amazonaws.com'
        s3_file_path = f"uploads/{img.filename}"

        if upload_to_aws(img.file, bucket_name, s3_file_path):
            # If the upload is successful, create the Place record in the database
            tags_str = ",".join(place.tags)
            place_db = Place(
                img=f"https://{bucket_name}{region_name}/{s3_file_path}",
                title=place.title,
                user_id=place.user_id,
                user_full_name=place.user_full_name,
                posted_date=datetime.utcnow(),
                content=place.content,
                rating_score=place.rating_score,
                tags=tags_str
            )

            db.add(place_db)
            db.commit()
            db.refresh(place_db)

            return place_db
        else:
            # Handle the case when the upload fails
            return create_response("error", "Failed to upload image to S3", data=None)
            # raise HTTPException(status_code=500, detail="Failed to upload image to S3")

    except Exception as e:
        # Handle other exceptions
        return create_response("error", f"Internal Server Error: {str(e)}", data=None)
        # raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")