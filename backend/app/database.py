from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Docker MySQL 用に 127.0.0.1 を使用（ポート公開されてる）
DATABASE_URL = os.getenv(
    "DATABASE_URL_LOCAL",
    os.getenv("DATABASE_URL", "mysql+pymysql://root:password@127.0.0.1:3306/customer_import")
)

# デバッグ用：接続先を表示
print(f"📌 Connecting to: {DATABASE_URL.replace('password', '***')}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
