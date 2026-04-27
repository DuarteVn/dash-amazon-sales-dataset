-- ============================================================
-- migrate.sql
-- Migra a tabela amazon_sales do schema bruto (importado via CSV)
-- para o schema definitivo usado pelo ORM.
--
-- Execução:
--   docker exec -i amazon_db mysql -u amazon_user -pamazon_pass amazon_sales_db < sql/migrate.sql
-- ============================================================

USE amazon_sales_db;

-- ── Etapa 1: Adicionar coluna PK auto-increment ──────────────
ALTER TABLE amazon_sales
    ADD COLUMN id INT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST;

-- ── Etapa 2: Adicionar coluna discount_pct (float limpa) ─────
ALTER TABLE amazon_sales
    ADD COLUMN discount_pct FLOAT NULL AFTER discount_percentage;

-- ── Etapa 3: Converter preços (remover ₹ e vírgulas → FLOAT) ─
ALTER TABLE amazon_sales
    ADD COLUMN discounted_price_f FLOAT NULL,
    ADD COLUMN actual_price_f     FLOAT NULL,
    ADD COLUMN rating_f           FLOAT NULL,
    ADD COLUMN rating_count_i     INT   NULL;

UPDATE amazon_sales SET
    discounted_price_f = NULLIF(CAST(REGEXP_REPLACE(discounted_price,   '[^0-9.]', '') AS DECIMAL(12,2)), 0),
    actual_price_f     = NULLIF(CAST(REGEXP_REPLACE(actual_price,       '[^0-9.]', '') AS DECIMAL(12,2)), 0),
    discount_pct       = NULLIF(CAST(REGEXP_REPLACE(discount_percentage,'[^0-9.]', '') AS DECIMAL(6,2)),  0),
    rating_f           = NULLIF(CAST(REGEXP_REPLACE(rating,             '[^0-9.]', '') AS DECIMAL(3,1)),  0),
    rating_count_i     = NULLIF(CAST(REGEXP_REPLACE(rating_count,       '[^0-9]',  '') AS UNSIGNED),      0);

-- ── Etapa 4: Remover colunas antigas e renomear as novas ─────
ALTER TABLE amazon_sales
    DROP COLUMN discounted_price,
    DROP COLUMN actual_price,
    DROP COLUMN rating,
    DROP COLUMN rating_count,
    DROP COLUMN discount_percentage;

ALTER TABLE amazon_sales
    CHANGE discounted_price_f discounted_price FLOAT NULL,
    CHANGE actual_price_f     actual_price     FLOAT NULL,
    CHANGE rating_f           rating           FLOAT NULL,
    CHANGE rating_count_i     rating_count     INT   NULL;

-- ── Etapa 5: Ajustar tipo de category (TEXT → VARCHAR 255) ───
ALTER TABLE amazon_sales
    MODIFY category VARCHAR(255) NOT NULL DEFAULT '';

-- ── Etapa 6: Adicionar índices ────────────────────────────────
ALTER TABLE amazon_sales
    ADD INDEX idx_product_id   (product_id),
    ADD INDEX idx_category     (category),
    ADD INDEX idx_rating       (rating),
    ADD INDEX idx_rating_count (rating_count);

-- ── Verificação final ─────────────────────────────────────────
SELECT
    'Migração concluída!' AS status,
    COUNT(*) AS total_rows
FROM amazon_sales;

DESCRIBE amazon_sales;
