from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from .. import crud, models
from ..database import get_db, SessionLocal
from ..import_processor import process_import_job

router = APIRouter(prefix="/api/customers/upload", tags=["S3 Upload"])

# S3クライアント初期化
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'ap-northeast-1')
)

BUCKET_NAME = os.getenv('AWS_S3_BUCKET', 'customer-import-bucket')

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str = "text/csv"

class PresignedUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in: int

@router.post("/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(request: PresignedUrlRequest):
    try:
        date_prefix = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8]
        s3_key = f"uploads/{date_prefix}/{unique_id}_{request.filename}"
        
        expires_in = 900
        
        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': s3_key,
                'ContentType': request.content_type
            },
            ExpiresIn=expires_in
        )
        
        return PresignedUrlResponse(
            upload_url=upload_url,
            s3_key=s3_key,
            expires_in=expires_in
        )
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3エラー: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"予期しないエラー: {str(e)}")

class ImportFromS3Request(BaseModel):
    s3_key: str
    mapping: dict = {
        "name": "name",
        "email": "email",
        "phone": "phone",
        "address": "address"
    }

class ImportFromS3Response(BaseModel):
    import_id: int
    status: str
    message: str

def run_import_job(import_id: int, mapping: dict):
    """バックグラウンドタスク用のラッパー"""
    db = SessionLocal()
    try:
        process_import_job(import_id, mapping, [], db)
    except Exception as e:
        print(f"ERROR in background task: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

@router.post("/import-from-s3", response_model=ImportFromS3Response)
async def import_from_s3(
    request: ImportFromS3Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        filename = request.s3_key.split('/')[-1]
        
        db_import = crud.create_import(
            db=db,
            filename=filename,
            s3_key=request.s3_key
        )
        
        background_tasks.add_task(run_import_job, db_import.id, request.mapping)
        
        return ImportFromS3Response(
            import_id=db_import.id,
            status="processing",
            message=f"インポート処理を開始しました (ID: {db_import.id})"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"インポートエラー: {str(e)}")