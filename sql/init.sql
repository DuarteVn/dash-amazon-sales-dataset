-- ============================================================
-- DDL: Amazon Sales Dataset
-- Banco: amazon_sales_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS amazon_sales_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE amazon_sales_db;

CREATE TABLE IF NOT EXISTS amazon_sales (
    id               INT           NOT NULL AUTO_INCREMENT,
    product_id       VARCHAR(20)   NOT NULL,
    product_name     TEXT          NOT NULL,
    category         VARCHAR(255)  NOT NULL,
    discounted_price FLOAT         NULL,        -- Valor após desconto (ex: ₹999 → 999.0)
    actual_price     FLOAT         NULL,        -- Valor original
    discount_pct     FLOAT         NULL,        -- Percentual do desconto (ex: 64% → 64.0)
    rating           FLOAT         NULL,        -- Avaliação 0-5
    rating_count     INT           NULL,        -- Número de avaliações
    about_product    TEXT          NULL,
    user_id          TEXT          NULL,
    user_name        TEXT          NULL,
    review_id        TEXT          NULL,
    review_title     TEXT          NULL,
    review_content   TEXT          NULL,
    img_link         TEXT          NULL,
    product_link     TEXT          NULL,
    PRIMARY KEY (id),
    INDEX idx_product_id (product_id),
    INDEX idx_category   (category),
    INDEX idx_rating     (rating),
    INDEX idx_rating_count (rating_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
