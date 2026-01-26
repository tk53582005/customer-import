from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..s3_service import s3_service

router = APIRouter()


class PresignedUrlRequest(BaseModel):
    filename: str


class PresignedUrlResponse(BaseModel):
    url: str
    fields: dict
    key: str


@router.post("/presign", response_model=PresignedUrlResponse)
async def create_presigned_url(request: PresignedUrlRequest):
    """
    S3アップロード用の presigned URL を生成
    """
    result = s3_service.generate_presigned_url(request.filename)
    
    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate presigned URL"
        )
    
    return result
