"""
schemas.py
----------
Schemas Pydantic para validação e serialização das respostas da API.
"""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class ProductBase(BaseModel):
    product_id:       Optional[str]   = None
    product_name:     Optional[str]   = None
    category:         str
    discounted_price: Optional[float] = None
    actual_price:     Optional[float] = None
    discount_pct:     Optional[float] = None
    rating:           Optional[float] = None
    rating_count:     Optional[int]   = None
    img_link:         Optional[str]   = None
    product_link:     Optional[str]   = None

    model_config = {"from_attributes": True}


class ProductDetail(ProductBase):
    id:             int
    about_product:  Optional[str] = None
    review_title:   Optional[str] = None
    review_content: Optional[str] = None


# ─── Schemas de resposta das rotas específicas ────────────────

class TopProductSchema(BaseModel):
    product_id:   Optional[str]
    product_name: Optional[str]
    rating:       Optional[float]
    rating_count: Optional[int]

    model_config = {"from_attributes": True}


class KpiSchema(BaseModel):
    total_revenue:      float
    average_ticket:     float
    average_discount:   float
    best_rated_product: str


class CategorySchema(BaseModel):
    category: str
    count:    int


# ─── Novos schemas para gráficos avançados ────────────────────

class CategoryStatsSchema(BaseModel):
    """Para o Treemap: faturamento e desconto por categoria."""
    category:      str
    total_revenue: float
    avg_discount:  float
    product_count: int


class PricePointSchema(BaseModel):
    """Para o Boxplot: par (categoria, preço) de cada produto."""
    category:        str
    discounted_price: float


class WordFreqSchema(BaseModel):
    """Para o gráfico de palavras mais frequentes nos reviews."""
    word:  str
    count: int
