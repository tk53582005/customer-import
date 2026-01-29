from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Docker環境判定（DOCKER_ENV環境変数で判断）
is_docker = os.getenv("DOCKER_ENV", "false").lower() == "true"

if is_docker:
    # Docker環境: DATABASE_URL を使用（mysql:3306）
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@mysql:3306/customer_import")
else:
    # ローカル環境: DATABASE_URL_LOCAL を優先
    DATABASE_URL = os.getenv(
        "DATABASE_URL_LOCAL",
        os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/customer_import")
    )

# デバッグ用：接続先を表示
print(f"📌 Connecting to: {DATABASE_URL.replace('app_pass', '***').replace('password', '***')}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
