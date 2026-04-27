"""
routers/products.py
--------------------
Rotas relacionadas a produtos do Amazon Sales Dataset.

Endpoints:
  GET /products/top10             → Top 10 por rating_count
  GET /products/by-category       → Filtro por categoria (+ faixa de preço e rating mínimo)
  GET /products/categories        → Lista todas as categorias disponíveis
  GET /products/kpis              → Métricas principais (KPI Cards)
  GET /products/category-stats    → Faturamento e desconto médio por categoria (Treemap)
  GET /products/price-distribution → Preços por categoria (Boxplot)
  GET /products/review-words      → Palavras mais frequentes nos reviews (Top N)
  GET /products/                  → Listagem paginada com múltiplos filtros
"""

from __future__ import annotations

import re
from collections import Counter
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from database import get_db
from models import AmazonSale
from schemas import (
    ProductDetail,
    TopProductSchema,
    KpiSchema,
    CategorySchema,
    CategoryStatsSchema,
    PricePointSchema,
    WordFreqSchema,
)

router = APIRouter(prefix="/products", tags=["Products"])

# ── Stop-words básicas (sem NLTK) ─────────────────────────────
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "it", "this", "that", "was", "are", "be", "as",
    "i", "my", "we", "you", "he", "she", "they", "its", "not", "have",
    "has", "had", "by", "from", "so", "very", "good", "great", "product",
    "nice", "best", "use", "used", "using", "well", "also", "one", "get",
    "got", "would", "could", "like", "just", "can", "will", "do", "did",
    "if", "after", "but", "more", "than", "which", "been", "when", "all",
    "your", "our", "their", "his", "her", "no", "time", "price", "buy",
    "item", "value", "money", "quality", "Amazon", "amazon",
}


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/top10
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/top10", response_model=List[TopProductSchema], summary="Top 10 produtos por rating_count")
def get_top10_by_rating_count(db: Session = Depends(get_db)) -> List[TopProductSchema]:
    """Retorna os 10 produtos com maior número de avaliações (rating_count)."""
    rows = (
        db.query(
            AmazonSale.product_id,
            AmazonSale.product_name,
            AmazonSale.rating,
            AmazonSale.rating_count,
        )
        .filter(AmazonSale.rating_count.isnot(None))
        .order_by(AmazonSale.rating_count.desc())
        .limit(10)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado.")
    return [TopProductSchema.model_validate(row._asdict()) for row in rows]


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/by-category
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/by-category", response_model=List[ProductDetail], summary="Filtrar produtos por categoria")
def get_products_by_category(
    category:   str            = Query(...,  description="Nome exato ou parcial da categoria"),
    min_price:  Optional[float] = Query(None, description="Preço mínimo com desconto"),
    max_price:  Optional[float] = Query(None, description="Preço máximo com desconto"),
    min_rating: Optional[float] = Query(None, description="Rating mínimo (ex: 4.0)"),
    limit:      int             = Query(50,   ge=1, le=200),
    db:         Session         = Depends(get_db),
) -> List[ProductDetail]:
    """Filtra produtos por categoria (busca parcial, case-insensitive)."""
    query = db.query(AmazonSale).filter(AmazonSale.category.ilike(f"%{category}%"))
    if min_price  is not None: query = query.filter(AmazonSale.discounted_price >= min_price)
    if max_price  is not None: query = query.filter(AmazonSale.discounted_price <= max_price)
    if min_rating is not None: query = query.filter(AmazonSale.rating >= min_rating)
    results = query.order_by(AmazonSale.rating.desc()).limit(limit).all()
    if not results:
        raise HTTPException(status_code=404, detail=f"Nenhum produto encontrado para '{category}'.")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/categories
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/categories", response_model=List[CategorySchema], summary="Lista todas as categorias")
def get_categories(db: Session = Depends(get_db)) -> List[CategorySchema]:
    """Retorna todas as categorias com contagem de produtos."""
    rows = (
        db.query(AmazonSale.category, func.count(AmazonSale.id).label("count"))
        .group_by(AmazonSale.category)
        .order_by(func.count(AmazonSale.id).desc())
        .all()
    )
    return [CategorySchema(category=r.category, count=r.count) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/kpis
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/kpis", response_model=KpiSchema, summary="KPI Cards do Dashboard")
def get_kpis(db: Session = Depends(get_db)) -> KpiSchema:
    """Calcula faturamento total, ticket médio, desconto médio e melhor avaliado."""
    result = db.execute(
        text("""
            SELECT
                COALESCE(SUM(discounted_price), 0) AS total_revenue,
                COALESCE(AVG(discounted_price), 0) AS average_ticket,
                COALESCE(AVG(discount_pct),    0) AS average_discount
            FROM amazon_sales
            WHERE discounted_price IS NOT NULL
        """)
    ).fetchone()
    best_rated = (
        db.query(AmazonSale.product_name)
        .filter(AmazonSale.rating.isnot(None))
        .order_by(AmazonSale.rating.desc(), AmazonSale.rating_count.desc())
        .first()
    )
    return KpiSchema(
        total_revenue=round(result.total_revenue, 2),
        average_ticket=round(result.average_ticket, 2),
        average_discount=round(result.average_discount, 2),
        best_rated_product=best_rated.product_name if best_rated else "N/A",
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/category-stats  (NOVO — Treemap)
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/category-stats",
    response_model=List[CategoryStatsSchema],
    summary="Faturamento e desconto por categoria (Treemap)",
)
def get_category_stats(
    top_n: int = Query(20, ge=5, le=50, description="Limita às N categorias com maior faturamento"),
    db: Session = Depends(get_db),
) -> List[CategoryStatsSchema]:
    """
    Agrega por categoria:
      - total_revenue  : soma do discounted_price
      - avg_discount   : média do discount_pct
      - product_count  : número de SKUs

    Usado para montar o Treemap no frontend.
    """
    rows = db.execute(
        text("""
            SELECT
                category,
                ROUND(SUM(discounted_price), 2)  AS total_revenue,
                ROUND(AVG(discount_pct),     2)  AS avg_discount,
                COUNT(*)                         AS product_count
            FROM amazon_sales
            WHERE discounted_price IS NOT NULL
              AND category IS NOT NULL
              AND category != ''
            GROUP BY category
            ORDER BY total_revenue DESC
            LIMIT :top_n
        """),
        {"top_n": top_n},
    ).fetchall()

    return [
        CategoryStatsSchema(
            category=r.category,
            total_revenue=r.total_revenue or 0.0,
            avg_discount=r.avg_discount or 0.0,
            product_count=r.product_count,
        )
        for r in rows
    ]


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/price-distribution  (NOVO — Boxplot)
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/price-distribution",
    response_model=List[PricePointSchema],
    summary="Distribuição de preços por categoria (Boxplot)",
)
def get_price_distribution(
    top_n: int = Query(10, ge=3, le=30, description="Top N categorias por volume de produtos"),
    db:    Session = Depends(get_db),
) -> List[PricePointSchema]:
    """
    Retorna pares (categoria, discounted_price) para as top_n categorias.
    O frontend usa esses pontos brutos para montar um Boxplot.
    """
    # Pegar as top_n categorias por volume
    top_cats = db.execute(
        text("""
            SELECT category
            FROM amazon_sales
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY COUNT(*) DESC
            LIMIT :top_n
        """),
        {"top_n": top_n},
    ).fetchall()

    if not top_cats:
        return []

    cat_list = [r.category for r in top_cats]
    placeholders = ", ".join([f":cat{i}" for i in range(len(cat_list))])
    params = {f"cat{i}": cat for i, cat in enumerate(cat_list)}

    rows = db.execute(
        text(f"""
            SELECT category, discounted_price
            FROM amazon_sales
            WHERE category IN ({placeholders})
              AND discounted_price IS NOT NULL
              AND discounted_price > 0
        """),
        params,
    ).fetchall()

    return [PricePointSchema(category=r.category, discounted_price=r.discounted_price) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/review-words  (NOVO — Word Frequency)
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/review-words",
    response_model=List[WordFreqSchema],
    summary="Palavras mais frequentes nos reviews",
)
def get_review_words(
    top_n:    int          = Query(25,   ge=5, le=50,  description="Top N palavras"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    db:       Session       = Depends(get_db),
) -> List[WordFreqSchema]:
    """
    Processa review_content dos produtos, remove stop-words e retorna
    as top_n palavras mais frequentes. Processamento feito em Python
    para flexibilidade (sem dependência de NLTK no container).
    """
    query = (
        db.query(AmazonSale.review_content)
        .filter(AmazonSale.review_content.isnot(None))
    )
    if category:
        query = query.filter(AmazonSale.category.ilike(f"%{category}%"))

    rows = query.limit(300).all()  # Limitar para não sobrecarregar

    word_counter: Counter = Counter()
    for (review,) in rows:
        if not review:
            continue
        # Tokenização simples: só letras, lowercase, mínimo 3 chars
        words = re.findall(r"\b[a-zA-Z]{3,}\b", review.lower())
        clean = [w for w in words if w not in _STOP_WORDS]
        word_counter.update(clean)

    return [
        WordFreqSchema(word=word, count=count)
        for word, count in word_counter.most_common(top_n)
    ]


# ─────────────────────────────────────────────────────────────────────────────
# GET /products/
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[ProductDetail], summary="Listagem paginada com filtros")
def list_products(
    category:   Optional[str]   = Query(None),
    min_rating: Optional[float] = Query(None),
    min_price:  Optional[float] = Query(None),
    max_price:  Optional[float] = Query(None),
    skip:       int              = Query(0,  ge=0),
    limit:      int              = Query(20, ge=1, le=100),
    db:         Session          = Depends(get_db),
) -> List[ProductDetail]:
    """Listagem geral paginada com filtros opcionais."""
    query = db.query(AmazonSale)
    if category:    query = query.filter(AmazonSale.category.ilike(f"%{category}%"))
    if min_rating:  query = query.filter(AmazonSale.rating >= min_rating)
    if min_price:   query = query.filter(AmazonSale.discounted_price >= min_price)
    if max_price:   query = query.filter(AmazonSale.discounted_price <= max_price)
    return query.offset(skip).limit(limit).all()
