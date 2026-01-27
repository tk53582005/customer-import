from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import imports, uploads
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Customer Import API")

# CORS設定
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(imports.router, prefix="/api", tags=["imports"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])

@app.get("/")
def read_root():
    return {"message": "Customer Import API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """起動時にテーブル作成"""
    from .database import engine, Base
    Base.metadata.create_all(bind=engine)
