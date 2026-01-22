from typing import Dict, Any, List
import re

def normalize_value(value: Any, rule: str) -> str:
    """値を正規化"""
    if value is None:
        return ""
    
    s = str(value).strip()
    
    if rule == "trim":
        return s
    elif rule == "email":
        return s.lower()
    elif rule == "phone":
        # ハイフン、スペース、括弧を除去
        return re.sub(r"[\s\-()（）]", "", s)
    
    return s

def validate_value(value: str, rule: str) -> str:
    """値をバリデーション（エラーメッセージを返す）"""
    if rule == "email":
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            return "メールアドレスの形式が不正です"
    elif rule == "date":
        # 簡易的な日付チェック
        if not re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", value):
            return "日付の形式が不正です (YYYY-MM-DD または YYYY/MM/DD)"
    
    return ""

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
    """文字列の類似度を計算（0.0 ~ 1.0）"""
    if not s1 or not s2:
        return 0.0
    
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    
    distance = levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)

def find_duplicate_candidates(
    new_row: Dict[str, Any],
    existing_customers: List[Dict[str, Any]],
    threshold: float = 0.85
) -> List[Dict[str, Any]]:
    """重複候補を検出"""
    candidates = []
    
    new_email = new_row.get("email", "")
    new_phone = new_row.get("phone", "")
    new_name = new_row.get("full_name", "")
    new_address = new_row.get("address_line1", "") or new_row.get("address", "")
    
    # 🔥 email完全一致チェック
    if new_email:
        for customer in existing_customers:
            if customer.get("email") == new_email:
                candidates.append({
                    "customer_id": customer["id"],
                    "match_reason": f"Email完全一致: {new_email}",
                    "similarity_score": 1.0
                })
                return candidates  # email完全一致があれば他は見ない
    
    # 🔥 phone完全一致チェック
    if new_phone:
        for customer in existing_customers:
            if customer.get("phone") == new_phone:
                candidates.append({
                    "customer_id": customer["id"],
                    "match_reason": f"電話番号完全一致: {new_phone}",
                    "similarity_score": 1.0
                })
                return candidates  # phone完全一致があれば他は見ない
    
    # 名前・住所の類似度チェック
    if not new_name:
        return candidates
    
    for customer in existing_customers:
        cust_name = customer.get("full_name", "")
        cust_address = customer.get("address_line1", "") or customer.get("address", "")
        
        if not cust_name:
            continue
        
        name_sim = similarity_score(new_name, cust_name)
        
        # 名前の類似度が閾値以上
        if name_sim >= threshold:
            reason = f"名前類似: {cust_name} (類似度: {name_sim:.2f})"
            
            # 住所もチェック
            if new_address and cust_address:
                addr_sim = similarity_score(new_address, cust_address)
                if addr_sim >= threshold:
                    reason += f" / 住所類似: {cust_address} (類似度: {addr_sim:.2f})"
                    combined_score = (name_sim + addr_sim) / 2
                else:
                    combined_score = name_sim * 0.7  # 住所が一致しない場合はスコア減
            else:
                combined_score = name_sim
            
            candidates.append({
                "customer_id": customer["id"],
                "match_reason": reason,
                "similarity_score": combined_score
            })
    
    # スコアでソート
    candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return candidates[:5]  # 上位5件まで
