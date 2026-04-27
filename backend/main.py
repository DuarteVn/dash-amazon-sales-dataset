"""
main.py
-------
Ponto de entrada da aplicação FastAPI.
Registra todos os routers e configura CORS para comunicação com o Streamlit.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import products

# ── Criação das tabelas (caso não existam) ────────────────────
Base.metadata.create_all(bind=engine)

# ── Instância da aplicação ────────────────────────────────────
app = FastAPI(
    title="Amazon Sales Dashboard API",
    description="API para análise do Amazon Sales Dataset",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Em produção, restringir ao domínio do Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(products.router)


# ── Health Check ──────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Amazon Sales API"}
