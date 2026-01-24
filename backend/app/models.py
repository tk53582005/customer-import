from sqlalchemy import Column, Integer, String, JSON, Enum, DECIMAL, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .database import Base
import enum


class ImportStatus(str, enum.Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RowStatus(str, enum.Enum):
    pending = "pending"
    inserted = "inserted"
    error = "error"
    candidate = "candidate"


class Resolution(str, enum.Enum):
    pending = "pending"
    merged = "merged"
    created_new = "created_new"
    ignored = "ignored"


class Import(Base):
    __tablename__ = "imports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(Enum(ImportStatus), default=ImportStatus.processing)
    total_rows = Column(Integer, default=0)
    inserted_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    candidate_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)  # 🆕 追加
    resolved_by = Column(String(100), nullable=True)  # 🆕 追加
    resolved_at = Column(DateTime(timezone=True), nullable=True)  # 🆕 追加
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ImportRow(Base):
    __tablename__ = "import_rows"

    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(Integer, ForeignKey("imports.id"), nullable=False)
    row_index = Column(Integer, nullable=False)
    raw_data = Column(JSON)
    mapped_data = Column(JSON)
    normalized_data = Column(JSON)
    validation_errors = Column(JSON)
    status = Column(Enum(RowStatus), default=RowStatus.pending)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255))
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DuplicateCandidate(Base):
    __tablename__ = "duplicate_candidates"

    id = Column(Integer, primary_key=True, index=True)
    import_row_id = Column(Integer, ForeignKey(
        "import_rows.id"), nullable=False)
    existing_customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False)
    match_reason = Column(String(255))
    similarity_score = Column(DECIMAL(3, 2))
    resolution = Column(Enum(Resolution), default=Resolution.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
