"""
models.py
---------
ORM (Object-Relational Mapping) para a tabela amazon_sales.
Schema alinhado com o resultado do migrate.sql (DESCRIBE amazon_sales).
"""

from sqlalchemy import Column, Integer, String, Float, Text
from database import Base


class AmazonSale(Base):
    __tablename__ = "amazon_sales"

    # ── Colunas na ordem exata do DESCRIBE ───────────────────
    id               = Column(Integer, primary_key=True, autoincrement=True)
    product_id       = Column(String(100), nullable=True,  index=True)
    product_name     = Column(Text,        nullable=True)
    category         = Column(String(255), nullable=False, index=True)
    discount_pct     = Column(Float,       nullable=True)
    about_product    = Column(Text,        nullable=True)
    user_id          = Column(Text,        nullable=True)
    user_name        = Column(Text,        nullable=True)
    review_id        = Column(Text,        nullable=True)
    review_title     = Column(Text,        nullable=True)
    review_content   = Column(Text,        nullable=True)
    img_link         = Column(Text,        nullable=True)
    product_link     = Column(Text,        nullable=True)
    discounted_price = Column(Float,       nullable=True)
    actual_price     = Column(Float,       nullable=True)
    rating           = Column(Float,       nullable=True, index=True)
    rating_count     = Column(Integer,     nullable=True, index=True)
