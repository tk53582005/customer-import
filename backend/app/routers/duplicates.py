from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, models
from ..database import get_db
import json

router = APIRouter(tags=["Duplicates"])

@router.get("/{import_id}", response_model=List[schemas.DuplicateCandidateResponse])
def get_duplicate_candidates(import_id: int, db: Session = Depends(get_db)):
    """重複候補一覧を取得"""
    candidates = crud.get_duplicate_candidates(db, import_id)
    
    result = []
    for candidate in candidates:
        # ImportRowから新規データ取得
        import_row = db.query(models.ImportRow).filter(
            models.ImportRow.id == candidate.import_row_id
        ).first()
        
        # 既存顧客取得
        existing_customer = crud.get_customer(db, candidate.existing_customer_id)
        
        # JSON文字列をdictに変換
        normalized_data = import_row.normalized_data if import_row else {}
        if isinstance(normalized_data, str):
            normalized_data = json.loads(normalized_data)
        
        result.append(schemas.DuplicateCandidateResponse(
            id=candidate.id,
            import_row_id=candidate.import_row_id,
            existing_customer_id=candidate.existing_customer_id,
            existing_customer={
                "id": existing_customer.id,
                "full_name": existing_customer.full_name,
                "email": existing_customer.email,
                "phone": existing_customer.phone,
                "address": existing_customer.address
            },
            new_data=normalized_data,
            match_reason=candidate.match_reason,
            similarity_score=float(candidate.similarity_score),
            resolution=candidate.resolution.value
        ))
    
    return result

@router.post("/{candidate_id}/resolve")
def resolve_duplicate(
    candidate_id: int,
    request: schemas.CandidateResolveRequest,
    db: Session = Depends(get_db)
):
    """重複を解決"""
    candidate = db.query(models.DuplicateCandidate).filter(
        models.DuplicateCandidate.id == candidate_id
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    if request.action == "merged":
        # 既存顧客にマージ
        import_row = db.query(models.ImportRow).filter(
            models.ImportRow.id == candidate.import_row_id
        ).first()
        
        existing_customer = crud.get_customer(db, candidate.existing_customer_id)
        
        # 新規データで既存顧客を更新
        normalized_data = import_row.normalized_data if import_row else {}
        if isinstance(normalized_data, str):
            normalized_data = json.loads(normalized_data)
        
        for key, value in normalized_data.items():
            if value and hasattr(existing_customer, key):
                setattr(existing_customer, key, value)
        
        db.commit()
        
        # 解決済みにマーク
        crud.resolve_duplicate(db, candidate_id, "merged", existing_customer.id)
        
        return {"status": "merged", "customer_id": existing_customer.id}
    
    elif request.action == "created_new":
        # 新規顧客として作成
        import_row = db.query(models.ImportRow).filter(
            models.ImportRow.id == candidate.import_row_id
        ).first()
        
        normalized_data = import_row.normalized_data if import_row else {}
        if isinstance(normalized_data, str):
            normalized_data = json.loads(normalized_data)
        
        new_customer = crud.create_customer(
            db=db,
            full_name=normalized_data.get("full_name"),
            email=normalized_data.get("email"),
            phone=normalized_data.get("phone"),
            address=normalized_data.get("address")
        )
        
        # 解決済みにマーク
        crud.resolve_duplicate(db, candidate_id, "created_new", new_customer.id)
        
        return {"status": "created_new", "customer_id": new_customer.id}
    
    elif request.action == "ignored":
        # 無視
        crud.resolve_duplicate(db, candidate_id, "ignored")
        return {"status": "ignored"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
