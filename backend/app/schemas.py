from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

# リクエストスキーマ
class ImportCreate(BaseModel):
    filename: str

class ImportRunRequest(BaseModel):
    mapping: Dict[str, str]
    rows: List[Dict[str, Any]]

class CandidateResolveRequest(BaseModel):
    action: str  # "merged" | "created_new" | "ignored"

# レスポンススキーマ
class ImportCreateResponse(BaseModel):
    import_id: int

class ImportRunResponse(BaseModel):
    inserted: int
    errors: int
    candidates: int

class ImportStatusResponse(BaseModel):
    id: int
    filename: str
    status: str
    total_rows: int
    inserted_count: int
    error_count: int
    candidate_count: int
    created_at: datetime

class DuplicateCandidateResponse(BaseModel):
    id: int
    import_row_id: int
    existing_customer_id: int
    existing_customer: Dict[str, Any]
    new_data: Dict[str, Any]
    match_reason: str
    similarity_score: float
    resolution: str

    class Config:
        from_attributes = True
