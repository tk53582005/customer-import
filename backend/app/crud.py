from sqlalchemy.orm import Session
from . import models
from typing import List, Dict, Optional

def create_import(db: Session, filename: str, s3_key: Optional[str] = None) -> models.Import:
    """インポートレコードを作成"""
    db_import = models.Import(filename=filename, s3_key=s3_key)
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

def get_import_rows(db: Session, import_id: int) -> List[models.ImportRow]:
    """インポート行のリストを取得"""
    return db.query(models.ImportRow).filter(models.ImportRow.import_id == import_id).all()

def create_candidate(
    db: Session,
    import_id: int,
    row_index: int,
    customer_id: int,
    match_type: str,
    similarity_score: float
) -> models.DuplicateCandidate:
    """候補レコードを作成"""
    db_candidate = models.DuplicateCandidate(
        import_id=import_id,
        row_index=row_index,
        customer_id=customer_id,
        match_type=match_type,
        similarity_score=similarity_score
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def get_candidates(db: Session, import_id: int) -> List[models.DuplicateCandidate]:
    """候補リストを取得"""
    return db.query(models.DuplicateCandidate).filter(models.DuplicateCandidate.import_id == import_id).all()

def resolve_candidate(db: Session, candidate_id: int, action: str) -> models.DuplicateCandidate:
    """候補を解決"""
    db_candidate = db.query(models.DuplicateCandidate).filter(models.DuplicateCandidate.id == candidate_id).first()
    if db_candidate:
        db_candidate.status = "resolved"
        db_candidate.resolution_action = action
        db.commit()
        db.refresh(db_candidate)
    return db_candidate

def create_customer(
    db: Session,
    full_name: str,
    email: Optional[str],
    phone: Optional[str],
    address: Optional[str]
) -> models.Customer:
    """顧客を作成"""
    db_customer = models.Customer(
        full_name=full_name,
        email=email,
        phone=phone,
        address=address
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_customer(db: Session, customer_id: int) -> models.Customer:
    """顧客を取得"""
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def update_customer(
    db: Session,
    customer_id: int,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None
) -> models.Customer:
    """顧客を更新"""
    db_customer = get_customer(db, customer_id)
    if db_customer:
        if full_name is not None:
            db_customer.full_name = full_name
        if email is not None:
            db_customer.email = email
        if phone is not None:
            db_customer.phone = phone
        if address is not None:
            db_customer.address = address
        db.commit()
        db.refresh(db_customer)
    return db_customer

def get_all_customers(db: Session) -> List[models.Customer]:
    """全顧客を取得"""
    return db.query(models.Customer).all()