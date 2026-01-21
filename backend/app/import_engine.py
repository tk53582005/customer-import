import re
from typing import Dict, List, Any, Optional
from datetime import datetime

def levenshtein_distance(s1: str, s2: str) -> int:
    """Levenshtein距離を計算"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def similarity_score(s1: str, s2: str) -> float:
    """類似度スコアを計算（0.0-1.0）"""
    if not s1 or not s2:
        return 0.0
    
    s1_lower = s1.lower().strip()
    s2_lower = s2.lower().strip()
    
    if s1_lower == s2_lower:
        return 1.0
    
    distance = levenshtein_distance(s1_lower, s2_lower)
    max_len = max(len(s1_lower), len(s2_lower))
    
    if max_len == 0:
        return 0.0
    
    return 1.0 - (distance / max_len)

def normalize_value(value: Any, normalizer_type: str) -> Any:
    """値を正規化"""
    if value is None or value == "":
        return None
    
    str_value = str(value)
    
    if normalizer_type == "trim":
        return str_value.strip()
    elif normalizer_type == "lower":
        return str_value.lower()
    elif normalizer_type == "upper":
        return str_value.upper()
    elif normalizer_type == "digits_only":
        return re.sub(r'\D', '', str_value)
    
    return str_value

def validate_value(value: Any, validator_type: str) -> Optional[str]:
    """値を検証してエラーメッセージを返す"""
    if value is None or value == "":
        return None
    
    str_value = str(value)
    
    if validator_type == "email":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, str_value):
            return "Invalid email format"
    elif validator_type == "date":
        # 簡易的な日付チェック
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{2}/\d{2}/\d{4}$',
        ]
        if not any(re.match(pattern, str_value) for pattern in date_patterns):
            return "Invalid date format"
    
    return None

def find_duplicate_candidates(
    new_row: Dict[str, Any],
    existing_customers: List[Dict[str, Any]],
    threshold: float = 0.85
) -> List[Dict[str, Any]]:
    """重複候補を検出"""
    candidates = []
    
    # email/phoneがあれば候補検出しない（完全一致で処理）
    if new_row.get("email") or new_row.get("phone"):
        return candidates
    
    new_name = new_row.get("full_name", "")
    new_address = new_row.get("address", "")
    
    if not new_name:
        return candidates
    
    for customer in existing_customers:
        cust_name = customer.get("full_name", "")
        cust_address = customer.get("address", "")
        
        # 名前の類似度
        name_sim = similarity_score(new_name, cust_name)
        
        # 住所の類似度
        address_sim = 0.0
        if new_address and cust_address:
            address_sim = similarity_score(new_address, cust_address)
        
        # 総合スコア（名前重視）
        total_score = name_sim * 0.7 + address_sim * 0.3
        
        if total_score >= threshold:
            candidates.append({
                "customer_id": customer.get("id"),
                "customer": customer,
                "match_reason": f"Similar name ({name_sim:.2f}) and address ({address_sim:.2f})",
                "similarity_score": round(total_score, 2)
            })
    
    return candidates
