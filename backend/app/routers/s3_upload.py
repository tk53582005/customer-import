from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/customers/upload", tags=["S3 Upload"])

# S3クライアント初期化
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'ap-northeast-1')
)

# 修正: AWS_S3_BUCKET を読み込む
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
    """
    S3へのアップロード用presigned URLを生成
    
    Args:
        request: ファイル名とcontent-type
    
    Returns:
        upload_url: アップロード先URL
        s3_key: S3オブジェクトキー
        expires_in: URL有効期限(秒)
    """
    try:
        # S3キー生成: uploads/{date}/{uuid}_{filename}
        date_prefix = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8]
        s3_key = f"uploads/{date_prefix}/{unique_id}_{request.filename}"
        
        # presigned URL生成（有効期限: 15分）
        expires_in = 900  # 15 minutes
        
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

class ImportFromS3Response(BaseModel):
    job_id: str
    status: str
    message: str

@router.post("/import-from-s3", response_model=ImportFromS3Response)
async def import_from_s3(request: ImportFromS3Request):
    """
    S3からファイルをダウンロードしてインポート実行
    
    Args:
        request: S3オブジェクトキー
    
    Returns:
        job_id: ジョブID
        status: ステータス
        message: メッセージ
    """
    try:
        # TODO: 実際のインポート処理を実装
        # 1. S3からファイルをダウンロード
        # 2. CSVを解析
        # 3. DBにインポート
        
        # 仮のレスポンス
        import uuid
        job_id = str(uuid.uuid4())
        
        return ImportFromS3Response(
            job_id=job_id,
            status="processing",
            message=f"インポート処理を開始しました (S3キー: {request.s3_key})"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"インポートエラー: {str(e)}")
