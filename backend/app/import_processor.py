from sqlalchemy.orm import Session
from . import crud, models
from .import_engine import normalize_value, validate_value, find_duplicate_candidates


def empty_to_none(value):
    """空文字列をNoneに変換（UNIQUE制約対策）"""
    if value == "" or value is None:
        return None
    return value


def process_import_job(import_id: int, mapping: dict, rows: list, db: Session):
    """
    バックグラウンドでインポート処理を実行
    """
    try:
        # ステータスを processing に更新（念のため）
        db_import = crud.get_import(db, import_id)
        if not db_import:
            return

        db_import.status = models.ImportStatus.processing
        db.commit()

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

            # 正規化
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
                existing_customer = crud.get_customer_by_email(
                    db, normalized_data["email"])
            elif normalized_data.get("phone"):
                existing_customer = crud.get_customer_by_phone(
                    db, normalized_data["phone"])

            if existing_customer:
                # 既存顧客更新
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
                candidates = find_duplicate_candidates(
                    normalized_data, existing_customers_dict)

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

        # 成功: ステータスを completed に更新
        crud.update_import_status(
            db, import_id, "completed",
            total_rows=len(rows),
            inserted_count=inserted_count,
            error_count=error_count,
            candidate_count=candidate_count
        )

    except Exception as e:
        # 失敗: ステータスを failed に更新
        db_import = crud.get_import(db, import_id)
        if db_import:
            db_import.status = models.ImportStatus.failed
            db_import.error_message = str(e)  # エラー詳細を保存
            db.commit()
