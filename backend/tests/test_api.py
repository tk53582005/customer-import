import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    """ヘルスチェックAPIのテスト"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root(client):
    """ルートエンドポイントのテスト"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_get_import_history(client):
    """インポート履歴取得APIのテスト"""
    response = client.get("/api/imports/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_presigned_url_generation(client):
    """presigned URL生成APIのテスト"""
    response = client.post(
        "/api/customers/upload/presigned-url",
        json={
            "filename": "test.csv",
            "content_type": "text/csv"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "upload_url" in data
    assert "s3_key" in data
    assert "expires_in" in data
