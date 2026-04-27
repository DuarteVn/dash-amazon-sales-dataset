"""
database.py
-----------
Configuração da conexão com MySQL via SQLAlchemy.
Expõe: engine, SessionLocal, Base, get_db (dependency injection FastAPI).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://amazon_user:amazon_pass@db:3306/amazon_sales_db",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Verifica a conexão antes de usar
    pool_recycle=300,         # Recicla conexões a cada 5 min
    echo=False,               # True → loga SQL (só para debug)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ─── Dependency para injeção nas rotas ───────────────────────
def get_db():
    """Gera uma sessão de banco e garante o fechamento ao fim da request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
