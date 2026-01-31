from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/imports", tags=["Import History"])

@router.get("/", response_model=List[schemas.ImportStatusResponse])
def get_import_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """インポート履歴一覧を取得"""
    imports = db.query(models.Import).order_by(
        models.Import.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        schemas.ImportStatusResponse(
            id=imp.id,
            filename=imp.filename,
            status=imp.status.value,
            total_rows=imp.total_rows or 0,
            inserted_count=imp.inserted_count or 0,
            error_count=imp.error_count or 0,
            candidate_count=imp.candidate_count or 0,
            error_message=imp.error_message,
            created_by=None,
            resolved_by=None,
            resolved_at=None,
            s3_key=imp.s3_key,
            created_at=imp.created_at
        )
        for imp in imports
    ]
