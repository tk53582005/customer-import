import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'ap-northeast-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET')
    
    def generate_presigned_url(self, file_name: str, expiration: int = 3600) -> Optional[dict]:
        """
        Presigned URL を生成（フロントエンドが直接S3にアップロードするため）
        """
        try:
            object_key = f"uploads/{file_name}"
            
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                ExpiresIn=expiration
            )
            
            return {
                "url": presigned_post["url"],
                "fields": presigned_post["fields"],
                "key": object_key
            }
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def download_file(self, s3_key: str) -> Optional[bytes]:
        """
        S3からファイルをダウンロード
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            print(f"Error downloading file from S3: {e}")
            return None
    
    def delete_file(self, s3_key: str) -> bool:
        """
        S3からファイルを削除
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False


# シングルトンインスタンス
s3_service = S3Service()
