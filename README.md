# 📦 Amazon Sales Dashboard

> **Estudo prático de FastAPI** — construção de uma API REST completa com MySQL, dashboard interativo em Streamlit e (em breve) um **modelo de previsão de vendas com Machine Learning**.

Stack: **FastAPI · SQLAlchemy · MySQL · Streamlit · Docker**

---

##  Objetivo

Este projeto foi desenvolvido como estudo dos principais conceitos do **FastAPI**, abrangendo:

- Criação de rotas REST com tipagem via **Pydantic**
- Integração com banco de dados relacional usando **SQLAlchemy (ORM)**
- Containerização completa com **Docker + Docker Compose**
- Consumo da API em um **dashboard analítico** com Streamlit
- *(Em desenvolvimento)* **Modelo de previsão de vendas** com base nos dados históricos do dataset

---

## Estrutura do Projeto

```
dash-amazon-sales-dataset/
├── docker-compose.yml
├── .env
├── sql/
│   └── init.sql                  ← DDL da tabela (executado automaticamente)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   ← Ponto de entrada FastAPI
│   ├── database.py               ← Conexão SQLAlchemy
│   ├── models.py                 ← ORM models
│   ├── schemas.py                ← Pydantic schemas
│   └── routers/
│       └── products.py           ← Todas as rotas de produtos
└── frontend/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py                    ← Dashboard Streamlit
```

---

## Como Subir o Ambiente

```bash
# 1. Clonar o repositório
git clone https://github.com/<seu-usuario>/dash-amazon-sales-dataset.git
cd dash-amazon-sales-dataset

# 2. Subir todos os containers
docker-compose up --build -d

# 3. Verificar status
docker-compose ps
```

| Serviço   | URL                        |
|-----------|----------------------------|
| MySQL     | `localhost:3306`           |
| FastAPI   | http://localhost:8000/docs |
| Streamlit | http://localhost:8501      |

---

## 📡 Endpoints da API

| Método | Rota                        | Descrição                             |
|--------|-----------------------------|---------------------------------------|
| GET    | `/health`                   | Health check                          |
| GET    | `/products/top10`           | Top 10 produtos por avaliações        |
| GET    | `/products/by-category`     | Filtrar por categoria, preço e rating |
| GET    | `/products/categories`      | Lista categorias com contagem         |
| GET    | `/products/kpis`            | KPIs do dashboard                     |
| GET    | `/products/`                | Listagem paginada com filtros         |
| GET    | `/docs`                     | Swagger UI interativo                 |

### Exemplos de chamada

```bash
# Top 10 produtos mais avaliados
curl http://localhost:8000/products/top10

# Filtrar por categoria com rating mínimo
curl "http://localhost:8000/products/by-category?category=Electronics&min_rating=4.0&min_price=100"

# KPIs gerais
curl http://localhost:8000/products/kpis
```

---

## Limpeza dos Dados

O CSV do Amazon Sales Dataset contém campos de preço no formato indiano (ex: `₹1,299`) e percentuais com `%`. É necessário limpá-los antes da inserção.

### Script Python (recomendado)

```python
import pandas as pd
import re

df = pd.read_csv("amazon.csv")

def clean_price(value) -> float | None:
    if pd.isna(value): return None
    cleaned = re.sub(r"[^\d.]", "", str(value))
    try: return float(cleaned)
    except ValueError: return None

def clean_percentage(value) -> float | None:
    if pd.isna(value): return None
    cleaned = re.sub(r"[^\d.]", "", str(value))
    try: return float(cleaned)
    except ValueError: return None

def clean_rating_count(value) -> int | None:
    if pd.isna(value): return None
    cleaned = re.sub(r"[^\d]", "", str(value))
    try: return int(cleaned)
    except ValueError: return None

df["discounted_price"] = df["discounted_price"].apply(clean_price)
df["actual_price"]     = df["actual_price"].apply(clean_price)
df["discount_pct"]     = df["discount_percentage"].apply(clean_percentage)
df["rating"]           = pd.to_numeric(df["rating"], errors="coerce")
df["rating_count"]     = df["rating_count"].apply(clean_rating_count)
df = df.rename(columns={"discount_percentage": "discount_pct"})

df.to_csv("amazon_clean.csv", index=False, encoding="utf-8")
print(f"✅ {len(df)} linhas exportadas para amazon_clean.csv")
```

---

## 🔮 Previsão de Vendas *(em desenvolvimento)*

A próxima etapa do projeto é a implementação de um **modelo de Machine Learning** para previsão de vendas, que será integrado como um novo módulo da API FastAPI.

Funcionalidades planejadas:
- Treinamento de modelo com dados históricos do dataset
- Endpoint `/forecast` para retornar previsões via API
- Visualização das previsões no dashboard Streamlit

---

## 🛑 Parar o Ambiente

```bash
docker-compose down          # Para os containers
docker-compose down -v       # Para e remove os volumes (apaga o banco)
```

---

## 📚 Conceitos de FastAPI Praticados

| Conceito | Onde é aplicado |
|---|---|
| `APIRouter` | `routers/products.py` |
| Schemas Pydantic | `schemas.py` |
| ORM com SQLAlchemy | `models.py` + `database.py` |
| Dependency Injection | `Depends(get_db)` nas rotas |
| Query Parameters tipados | Filtros em `/by-category` |
| Paginação | `/products/?skip=0&limit=100` |
| Documentação automática | `/docs` (Swagger UI) |
