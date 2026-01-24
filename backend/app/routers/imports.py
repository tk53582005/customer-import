from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime  # 🆕 追加
from .. import crud, schemas, models
from ..database import get_db
from ..import_engine import normalize_value, validate_value, find_duplicate_candidates
from ..import_processor import process_import_job

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
        raise HTTPException(
            status_code=400, detail="No customers data provided")

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
        candidates = find_duplicate_candidates(
            customer_data, existing_customers_dict)

        if candidates:
            # 候補あり
            results.append({
                "normalized": customer_data,
                "candidates": [
                    {
                        "candidateIndex": candidate["customer_id"],
                        "score": candidate["similarity_score"],
                        "reason": candidate["match_reason"]
                    }
                    for candidate in candidates
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
    customer_data = request.get("customer_data")

    if action not in ["merged", "created_new", "ignored"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    if not customer_data:
        raise HTTPException(
            status_code=400, detail="No customer data provided")

    # 🔥 ここから実装！
    if action == "merged":
        # 統合: 既存顧客を更新
        # email または phone で既存顧客を検索
        existing_customer = None

        email = empty_to_none(customer_data.get("email"))
        phone = empty_to_none(customer_data.get("phone"))

        if email:
            existing_customer = crud.get_customer_by_email(db, email)

        if not existing_customer and phone:
            existing_customer = crud.get_customer_by_phone(db, phone)

        if existing_customer:
            # 既存顧客のデータを更新
            if customer_data.get("full_name"):
                existing_customer.full_name = customer_data.get("full_name")
            if email:
                existing_customer.email = email
            if phone:
                existing_customer.phone = phone
            if customer_data.get("address_line1"):
                existing_customer.address = customer_data.get("address_line1")
            if customer_data.get("city"):
                existing_customer.city = customer_data.get("city")
            if customer_data.get("state"):
                existing_customer.state = customer_data.get("state")
            if customer_data.get("zip_code"):
                existing_customer.zip_code = customer_data.get("zip_code")

            db.commit()
            return {"status": "resolved", "action": "merged", "customer_id": existing_customer.id}
        else:
            raise HTTPException(
                status_code=404, detail="Existing customer not found")

    elif action == "created_new":
        # 新規作成
        customer_create = {
            "full_name": customer_data.get("full_name"),
            "email": empty_to_none(customer_data.get("email")),
            "phone": empty_to_none(customer_data.get("phone")),
            "address": customer_data.get("address_line1"),
            "city": customer_data.get("city"),
            "state": customer_data.get("state"),
            "zip_code": customer_data.get("zip_code")
        }
        new_customer = crud.create_customer(db, customer_create)
        return {"status": "resolved", "action": "created_new", "customer_id": new_customer.id}

    elif action == "ignored":
        # 無視: 何もしない
        return {"status": "resolved", "action": "ignored"}

    return {"status": "resolved", "action": action}

# 以下は既存のエンドポイント（そのまま残す）


@router.post("/imports", response_model=schemas.ImportCreateResponse)
def create_import(
    request: schemas.ImportCreate,
    db: Session = Depends(get_db),
    user_name: str = Header(None, alias="X-User-Name")
):
    """インポートを作成"""
    db_import = crud.create_import(db, filename=request.filename)

    # created_by を保存
    if user_name:
        db_import.created_by = user_name
        db.commit()

    return {"import_id": db_import.id}


@router.post("/imports/{import_id}/run", response_model=schemas.ImportRunResponse)
def run_import(
    import_id: int,
    request: schemas.ImportRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """インポートを実行（非同期版）"""
    db_import = crud.get_import(db, import_id)
    if not db_import:
        raise HTTPException(status_code=404, detail="Import not found")

    # ステータスを processing に更新
    db_import.status = models.ImportStatus.processing
    db.commit()

    # バックグラウンドタスクに追加
    background_tasks.add_task(
        process_import_job,
        import_id=import_id,
        mapping=request.mapping,
        rows=request.rows,
        db=db
    )

    # すぐにレスポンスを返す
    return {
        "inserted": 0,  # まだ処理中なので0
        "errors": 0,
        "candidates": 0
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
    db: Session = Depends(get_db),
    user_name: str = Header(None, alias="X-User-Name")  # 🆕 追加
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

    # 🆕 resolved_by と resolved_at を保存
    if user_name:
        db_import = crud.get_import(db, import_id)
        if db_import:
            db_import.resolved_by = user_name
            db_import.resolved_at = datetime.now()
            db.commit()

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
