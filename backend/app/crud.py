from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Dict, Any

def create_import(db: Session, filename: str) -> models.Import:
    """インポートレコードを作成"""
    db_import = models.Import(filename=filename)
    db.add(db_import)
    db.commit()
    db.refresh(db_import)
    return db_import

def get_import(db: Session, import_id: int) -> models.Import:
    """インポートレコードを取得"""
    return db.query(models.Import).filter(models.Import.id == import_id).first()

def update_import_status(
    db: Session,
    import_id: int,
    status: str,
    total_rows: int = 0,
    inserted_count: int = 0,
    error_count: int = 0,
    candidate_count: int = 0
):
    """インポートステータスを更新"""
    db_import = get_import(db, import_id)
    if db_import:
        db_import.status = status
        db_import.total_rows = total_rows
        db_import.inserted_count = inserted_count
        db_import.error_count = error_count
        db_import.candidate_count = candidate_count
        db.commit()
        db.refresh(db_import)
    return db_import

def create_import_row(
    db: Session,
    import_id: int,
    row_index: int,
    raw_data: Dict,
    mapped_data: Dict,
    normalized_data: Dict,
    validation_errors: List[str],
    status: str
) -> models.ImportRow:
    """インポート行を作成"""
    db_row = models.ImportRow(
        import_id=import_id,
        row_index=row_index,
        raw_data=raw_data,
        mapped_data=mapped_data,
        normalized_data=normalized_data,
        validation_errors=validation_errors,
        status=status
    )
    db.add(db_row)
    db.commit()
    db.refresh(db_row)
    return db_row

def create_customer(db: Session, customer_data: Dict[str, Any]) -> models.Customer:
    """顧客を作成"""
    db_customer = models.Customer(**customer_data)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customer_by_email(db: Session, email: str) -> models.Customer:
    """emailで顧客を検索"""
    return db.query(models.Customer).filter(models.Customer.email == email).first()

def get_customer_by_phone(db: Session, phone: str) -> models.Customer:
    """phoneで顧客を検索"""
    return db.query(models.Customer).filter(models.Customer.phone == phone).first()

def get_all_customers(db: Session) -> List[models.Customer]:
    """全顧客を取得"""
    return db.query(models.Customer).all()

def create_duplicate_candidate(
    db: Session,
    import_row_id: int,
    existing_customer_id: int,
    match_reason: str,
    similarity_score: float
) -> models.DuplicateCandidate:
    """重複候補を作成"""
    db_candidate = models.DuplicateCandidate(
        import_row_id=import_row_id,
        existing_customer_id=existing_customer_id,
        match_reason=match_reason,
        similarity_score=similarity_score
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def get_duplicate_candidates(db: Session, import_id: int) -> List[models.DuplicateCandidate]:
    """インポートに紐づく重複候補を取得"""
    return db.query(models.DuplicateCandidate).join(
        models.ImportRow
    ).filter(
        models.ImportRow.import_id == import_id
    ).all()

def resolve_duplicate_candidate(
    db: Session,
    candidate_id: int,
    action: str,
    new_customer_data: Dict[str, Any] = None
):
    """重複候補を解決"""
    candidate = db.query(models.DuplicateCandidate).filter(
        models.DuplicateCandidate.id == candidate_id
    ).first()
    
    if not candidate:
        return None
    
    if action == "merged":
        # 既存顧客を更新
        customer = db.query(models.Customer).filter(
            models.Customer.id == candidate.existing_customer_id
        ).first()
        if customer and new_customer_data:
            for key, value in new_customer_data.items():
                if value:  # 新しいデータがあれば更新
                    setattr(customer, key, value)
        candidate.resolution = models.Resolution.merged
        
    elif action == "created_new":
        # 新規顧客作成
        if new_customer_data:
            create_customer(db, new_customer_data)
        candidate.resolution = models.Resolution.created_new
        
    elif action == "ignored":
        candidate.resolution = models.Resolution.ignored
    
    db.commit()
    db.refresh(candidate)
    return candidate
