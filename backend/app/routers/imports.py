from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, models
from ..database import get_db
from ..import_engine import normalize_value, validate_value, find_duplicate_candidates

router = APIRouter()

def empty_to_none(value):
    """空文字列をNoneに変換（UNIQUE制約対策）"""
    if value == "" or value is None:
        return None
    return value

# 🔥 Lv3用の新しいエンドポイント
@router.post("/customers/import")
def import_customers(request: dict, db: Session = Depends(get_db)):
    """顧客データをインポート（Lv3フロントエンド用）"""
    customers = request.get("customers", [])
    
    if not customers:
        raise HTTPException(status_code=400, detail="No customers data provided")
    
    # 既存顧客を取得
    existing_customers = crud.get_all_customers(db)
    existing_customers_dict = [
        {
            "id": c.id,
            "full_name": c.full_name,
            "email": c.email,
            "phone": c.phone,
            "address_line1": c.address or "",
            "address_line2": "",
            "city": c.city,
            "state": c.state,
            "zip_code": c.zip_code
        }
        for c in existing_customers
    ]
    
    results = []
    
    for idx, customer_data in enumerate(customers):
        # 重複候補検出
        candidates = find_duplicate_candidates(customer_data, existing_customers_dict)
        
        if candidates:
            # 候補あり
            results.append({
                "normalized": customer_data,
                "candidates": [
                    {
                        "candidateIndex": idx,
                        "score": c["similarity_score"],
                        "reason": c["match_reason"]
                    }
                    for c in candidates
                ]
            })
        else:
            # 新規作成（空文字列をNoneに変換）
            customer_create = {
                "full_name": customer_data.get("full_name"),
                "email": empty_to_none(customer_data.get("email")),
                "phone": empty_to_none(customer_data.get("phone")),
                "address": customer_data.get("address_line1"),
                "city": customer_data.get("city"),
                "state": customer_data.get("state"),
                "zip_code": customer_data.get("zip_code")
            }
            crud.create_customer(db, customer_create)
            results.append({
                "normalized": customer_data,
                "candidates": []
            })
    
    return {
        "status": "success",
        "candidates": results
    }

@router.post("/customers/resolve/{row_index}")
def resolve_customer(row_index: int, request: dict, db: Session = Depends(get_db)):
    """候補解決（Lv3フロントエンド用）"""
    action = request.get("action")
    
    if action not in ["merged", "created_new", "ignored"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return {"status": "resolved", "action": action}

# 以下は既存のエンドポイント（そのまま残す）
@router.post("/imports", response_model=schemas.ImportCreateResponse)
def create_import(request: schemas.ImportCreate, db: Session = Depends(get_db)):
    """インポートを作成"""
    db_import = crud.create_import(db, filename=request.filename)
    return {"import_id": db_import.id}

@router.post("/imports/{import_id}/run", response_model=schemas.ImportRunResponse)
def run_import(
    import_id: int,
    request: schemas.ImportRunRequest,
    db: Session = Depends(get_db)
):
    """インポートを実行"""
    db_import = crud.get_import(db, import_id)
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    mapping = request.mapping
    rows = request.rows
    
    inserted_count = 0
    error_count = 0
    candidate_count = 0
    
    # 既存顧客を取得
    existing_customers = crud.get_all_customers(db)
    existing_customers_dict = [
        {
            "id": c.id,
            "full_name": c.full_name,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "city": c.city,
            "state": c.state,
            "zip_code": c.zip_code
        }
        for c in existing_customers
    ]
    
    for idx, row in enumerate(rows):
        raw_data = row
        mapped_data = {}
        normalized_data = {}
        validation_errors = []
        
        # マッピング
        for db_field, excel_col in mapping.items():
            if excel_col and excel_col in row:
                mapped_data[db_field] = row[excel_col]
        
        # 正規化（簡易版：trimのみ）
        for field, value in mapped_data.items():
            normalized_data[field] = normalize_value(value, "trim")
        
        # バリデーション
        if "email" in normalized_data and normalized_data["email"]:
            error = validate_value(normalized_data["email"], "email")
            if error:
                validation_errors.append(f"email: {error}")
        
        # エラーがあればエラー行として保存
        if validation_errors:
            crud.create_import_row(
                db, import_id, idx, raw_data, mapped_data,
                normalized_data, validation_errors, "error"
            )
            error_count += 1
            continue
        
        # email/phoneで完全一致チェック
        existing_customer = None
        if normalized_data.get("email"):
            existing_customer = crud.get_customer_by_email(db, normalized_data["email"])
        elif normalized_data.get("phone"):
            existing_customer = crud.get_customer_by_phone(db, normalized_data["phone"])
        
        if existing_customer:
            # 既存顧客あり → 更新
            for key, value in normalized_data.items():
                if value:
                    setattr(existing_customer, key, value)
            db.commit()
            
            crud.create_import_row(
                db, import_id, idx, raw_data, mapped_data,
                normalized_data, [], "inserted"
            )
            inserted_count += 1
        else:
            # 重複候補検出
            candidates = find_duplicate_candidates(normalized_data, existing_customers_dict)
            
            if candidates:
                # 候補あり
                db_row = crud.create_import_row(
                    db, import_id, idx, raw_data, mapped_data,
                    normalized_data, [], "candidate"
                )
                
                for candidate in candidates:
                    crud.create_duplicate_candidate(
                        db,
                        import_row_id=db_row.id,
                        existing_customer_id=candidate["customer_id"],
                        match_reason=candidate["match_reason"],
                        similarity_score=candidate["similarity_score"]
                    )
                
                candidate_count += 1
            else:
                # 新規作成
                customer_data = {
                    "full_name": normalized_data.get("full_name"),
                    "email": empty_to_none(normalized_data.get("email")),
                    "phone": empty_to_none(normalized_data.get("phone")),
                    "address": normalized_data.get("address"),
                    "city": normalized_data.get("city"),
                    "state": normalized_data.get("state"),
                    "zip_code": normalized_data.get("zip_code")
                }
                crud.create_customer(db, customer_data)
                
                crud.create_import_row(
                    db, import_id, idx, raw_data, mapped_data,
                    normalized_data, [], "inserted"
                )
                inserted_count += 1
    
    # ステータス更新
    crud.update_import_status(
        db, import_id, "completed",
        total_rows=len(rows),
        inserted_count=inserted_count,
        error_count=error_count,
        candidate_count=candidate_count
    )
    
    return {
        "inserted": inserted_count,
        "errors": error_count,
        "candidates": candidate_count
    }

@router.get("/imports/{import_id}", response_model=schemas.ImportStatusResponse)
def get_import_status(import_id: int, db: Session = Depends(get_db)):
    """インポートステータスを取得"""
    db_import = crud.get_import(db, import_id)
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")
    
    return db_import

@router.post("/imports/{import_id}/candidates/{candidate_id}/resolve")
def resolve_candidate(
    import_id: int,
    candidate_id: int,
    request: schemas.CandidateResolveRequest,
    db: Session = Depends(get_db)
):
    """重複候補を解決"""
    # 候補を取得
    candidate = db.query(models.DuplicateCandidate).filter(
        models.DuplicateCandidate.id == candidate_id
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # import_rowから新規データを取得
    import_row = db.query(models.ImportRow).filter(
        models.ImportRow.id == candidate.import_row_id
    ).first()
    
    new_customer_data = import_row.normalized_data if import_row else {}
    
    # 解決処理
    result = crud.resolve_duplicate_candidate(
        db, candidate_id, request.action, new_customer_data
    )
    
    return {"status": "resolved", "action": request.action}

@router.get("/imports/{import_id}/candidates")
def get_import_candidates(import_id: int, db: Session = Depends(get_db)):
    """インポートの重複候補を取得"""
    candidates = crud.get_duplicate_candidates(db, import_id)
    
    result = []
    for candidate in candidates:
        # import_rowを取得
        import_row = db.query(models.ImportRow).filter(
            models.ImportRow.id == candidate.import_row_id
        ).first()
        
        # 既存顧客を取得
        existing_customer = db.query(models.Customer).filter(
            models.Customer.id == candidate.existing_customer_id
        ).first()
        
        result.append({
            "id": candidate.id,
            "import_row_id": candidate.import_row_id,
            "existing_customer_id": candidate.existing_customer_id,
            "new_data": import_row.normalized_data if import_row else {},
            "existing_customer": {
                "id": existing_customer.id,
                "full_name": existing_customer.full_name,
                "email": existing_customer.email,
                "phone": existing_customer.phone,
                "address": existing_customer.address,
            } if existing_customer else {},
            "match_reason": candidate.match_reason,
            "similarity_score": float(candidate.similarity_score),
            "resolution": candidate.resolution,
        })
    
    return result
