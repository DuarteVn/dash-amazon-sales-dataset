"""
app.py — Amazon Sales Dashboard
────────────────────────────────
UX/UI refatorado com:
  • Tema Amazon Dark (laranja #FF9900)
  • KPI Cards
  • Treemap de Faturamento por Categoria
  • Top 10 Bar Chart
  • Boxplot de Distribuição de Preços
  • Correlação Desconto vs Rating (Scatter)
  • Word Frequency dos Reviews
  • Galeria de Produto com Cards (imagem + link)
"""

import os
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─── Configuração da página ───────────────────────────────────
st.set_page_config(
    page_title="Amazon Sales Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE: str = os.getenv("API_BASE_URL", "http://backend:8000")

# ─── Paleta Amazon ───────────────────────────────────────────
AMAZON_ORANGE  = "#FF9900"
AMAZON_DARK    = "#131921"
AMAZON_SURFACE = "#1A1D27"
PLOTLY_LAYOUT  = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#F0F2F6",
    margin=dict(l=20, r=20, t=30, b=20),
)


# ─────────────────────────────────────────────────────────────
# Funções de acesso à API
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def fetch_kpis() -> dict | None:
    try:
        r = requests.get(f"{API_BASE}/products/kpis", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro KPIs: {e}")
        return None


@st.cache_data(ttl=120)
def fetch_top10() -> list[dict]:
    try:
        r = requests.get(f"{API_BASE}/products/top10", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro Top 10: {e}")
        return []


@st.cache_data(ttl=120)
def fetch_categories() -> list[dict]:
    try:
        r = requests.get(f"{API_BASE}/products/categories", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro categorias: {e}")
        return []


@st.cache_data(ttl=120)
def fetch_category_stats(top_n: int = 20) -> list[dict]:
    try:
        r = requests.get(f"{API_BASE}/products/category-stats", params={"top_n": top_n}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro category-stats: {e}")
        return []


@st.cache_data(ttl=120)
def fetch_price_distribution(top_n: int = 10) -> list[dict]:
    try:
        r = requests.get(f"{API_BASE}/products/price-distribution", params={"top_n": top_n}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro price-distribution: {e}")
        return []


@st.cache_data(ttl=120)
def fetch_review_words(top_n: int = 25, category: str | None = None) -> list[dict]:
    params: dict = {"top_n": top_n}
    if category:
        params["category"] = category
    try:
        r = requests.get(f"{API_BASE}/products/review-words", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro review-words: {e}")
        return []


def fetch_by_category(
    category: str,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
) -> list[dict]:
    params: dict = {"category": category, "limit": 100}
    if min_price  is not None: params["min_price"]  = min_price
    if max_price  is not None: params["max_price"]  = max_price
    if min_rating is not None: params["min_rating"] = min_rating
    try:
        r = requests.get(f"{API_BASE}/products/by-category", params=params, timeout=10)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Erro by-category: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# CSS personalizado
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Header premium */
  .dashboard-header {
    background: linear-gradient(135deg, #131921 0%, #1A1D27 100%);
    border-bottom: 2px solid #FF9900;
    padding: 1.2rem 1.5rem;
    border-radius: 10px;
    margin-bottom: 1rem;
  }
  .dashboard-header h1 { color: #FF9900; margin: 0; font-size: 1.8rem; }
  .dashboard-header p  { color: #a0aec0; margin: 0; font-size: 0.85rem; }

  /* Cards de produto */
  .product-card {
    background: #1A1D27;
    border: 1px solid #2d3143;
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    transition: border-color 0.2s;
    height: 320px;
    overflow: hidden;
  }
  .product-card:hover { border-color: #FF9900; }
  .product-card img {
    width: 100%;
    height: 150px;
    object-fit: contain;
    border-radius: 8px;
    background: #0E1117;
  }
  .product-card .p-name {
    font-size: 0.75rem;
    color: #e2e8f0;
    margin: 8px 0 4px;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .product-card .p-rating {
    color: #FF9900;
    font-weight: 700;
    font-size: 0.85rem;
  }
  .product-card .p-price {
    color: #68d391;
    font-size: 0.85rem;
  }
  .product-card a {
    display: inline-block;
    margin-top: 6px;
    padding: 4px 12px;
    background: #FF9900;
    color: #131921 !important;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    text-decoration: none;
  }
  .product-card a:hover { background: #e68900; }

  /* KPI Cards */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 8px;
  }
  .kpi-card {
    background: linear-gradient(145deg, #1A1D27 0%, #0E1117 100%);
    border: 1px solid #2d3143;
    border-radius: 14px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.25s, transform 0.2s;
  }
  .kpi-card:hover {
    border-color: #FF9900;
    transform: translateY(-2px);
  }
  .kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
  }
  .kpi-revenue::before  { background: linear-gradient(90deg, #FF9900, #FF5733); }
  .kpi-ticket::before   { background: linear-gradient(90deg, #2ecc71, #16a085); }
  .kpi-discount::before { background: linear-gradient(90deg, #3498db, #8e44ad); }
  .kpi-best::before     { background: linear-gradient(90deg, #f39c12, #d35400); }
  .kpi-icon {
    font-size: 1.5rem;
    margin-bottom: 8px;
    display: block;
  }
  .kpi-label {
    color: #718096;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
    display: block;
  }
  .kpi-value {
    color: #F0F2F6;
    font-size: 1.55rem;
    font-weight: 800;
    line-height: 1;
    display: block;
  }
  .kpi-sub {
    color: #a0aec0;
    font-size: 0.7rem;
    margin-top: 6px;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* Section label */
  .section-label {
    color: #FF9900;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
  <h1>Amazon Sales Dashboard</h1>
  <p>Análise interativa · FastAPI + Streamlit + MySQL · 2026</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Sidebar — Navegação
# ─────────────────────────────────────────────────────────────
categories_raw   = fetch_categories()
category_options = [c["category"] for c in categories_raw] if categories_raw else []

with st.sidebar:
    # Logo Amazon — wordmark CSS (sem dependência de URL externa)
    st.markdown("""
    <div style="text-align:center; padding:20px 0 22px;">
      <div style="
        font-family: Arial Black, Arial, sans-serif;
        font-size: 1.65rem;
        font-weight: 900;
        color: #F0F2F6;
        letter-spacing: -1px;
        line-height: 1;
      ">amazon</div>
      <div style="
        color: #FF9900;
        font-size: 1.5rem;
        margin-top: -6px;
        letter-spacing: 2px;
        line-height: 0.8;
      ">&#8599;</div>
      <div style="color:#718096; font-size:0.65rem; margin-top:8px; letter-spacing:1px; text-transform:uppercase;">Sales Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Menu de navegação
    nav_items = [
        ("", "Overview",            "Dashboard",   True),
        ("", "Análise de Produtos", "Exploração detalhada por produto", False),
        ("", "Previsão de Vendas",  "Modelos preditivos de demanda",   False),
        ("", "Relatórios",          "Exportar e agendar relatórios",  False),
    ]

    for icon, label, tooltip, active in nav_items:
        if active:
            st.markdown(
                f"""
                <div style="
                  background: linear-gradient(90deg,#FF9900 3px,#1A1D27 3px);
                  border-radius:8px; padding:10px 14px; margin:4px 0;
                ">
                  <span style="font-size:1rem;">{icon}</span>
                  <span style="color:#F0F2F6; font-weight:600; margin-left:8px;">{label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            badge = (
                ' <span style="background:#2d3143;color:#718096;font-size:0.6rem;'
                
                'padding:2px 6px;border-radius:10px;margin-left:4px;"><br>Em breve</span>'
                if label == "Previsão de Vendas" else ""
            )
            st.markdown(
                f"""
                <div style="border-radius:8px; padding:10px 14px; margin:4px 0; opacity:0.5;">
                  <span style="font-size:1rem;">{icon}</span>
                  <span style="color:#a0aec0; margin-left:8px;">{label}</span>{badge}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    st.caption("🟠 Online · API conectada")


# ─────────────────────────────────────────────────────────────
# KPI Cards — HTML customizado
# ─────────────────────────────────────────────────────────────
kpis = fetch_kpis()
if kpis:
    best_name = kpis['best_rated_product']
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card kpi-revenue">
        <span class="kpi-icon">💰</span>
        <span class="kpi-label">Faturamento Total</span>
        <span class="kpi-value">₹ {kpis['total_revenue']:,.0f}</span>
        <span class="kpi-sub">Soma de todos os preços com desconto</span>
      </div>
      <div class="kpi-card kpi-ticket">
        <span class="kpi-icon">🎫</span>
        <span class="kpi-label">Ticket Médio</span>
        <span class="kpi-value">₹ {kpis['average_ticket']:,.2f}</span>
        <span class="kpi-sub">Média por produto vendido</span>
      </div>
      <div class="kpi-card kpi-discount">
        <span class="kpi-icon">🏷️</span>
        <span class="kpi-label">Desconto Médio</span>
        <span class="kpi-value">{kpis['average_discount']:.1f}%</span>
        <span class="kpi-sub">Média sobre o preço original</span>
      </div>
      <div class="kpi-card kpi-best">
        <span class="kpi-icon">⭐</span>
        <span class="kpi-label">Melhor Avaliado</span>
        <span class="kpi-value">★★★★★</span>
        <span class="kpi-sub" title="{best_name}">{best_name[:55]}…</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()






# ─────────────────────────────────────────────────────────────
# Linha 1: Sunburst + Top 10 Bar
# ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="medium")

with col_left:
    st.markdown('<p class="section-label">Faturamento por Categoria</p>', unsafe_allow_html=True)
    st.subheader("Top Categorias")

    # Lê o valor do slider do session_state (default 20 na primeira execução)
    _lp_n = st.session_state.get("lp_topn", 20)
    stats = fetch_category_stats(top_n=_lp_n)
    if stats:
        df_stats = pd.DataFrame(stats)
        # Limpar nome: pegar só o último nível do path (ex: "Mice" em vez de "Electronics|...|Mice")
        df_stats["cat_short"] = (
            df_stats["category"].str.split("|").str[-1].str.strip()
        )
        # Ordenar por faturamento crescente (Plotly inverte no eixo Y)
        df_stats = df_stats.sort_values("total_revenue", ascending=True)

        fig_lp = go.Figure()

        # ─ Cabo do pirulito (barra ultra-fina, usando scatter com mode='lines') ────
        for _, row in df_stats.iterrows():
            fig_lp.add_trace(
                go.Scatter(
                    x=[0, row["total_revenue"]],
                    y=[row["cat_short"], row["cat_short"]],
                    mode="lines",
                    line=dict(color="#2d3748", width=2),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        # ─ Bola (marcador) com valor interno ─────────────────────────────
        fig_lp.add_trace(
            go.Scatter(
                x=df_stats["total_revenue"],
                y=df_stats["cat_short"],
                mode="markers+text",
                marker=dict(
                    size=18,
                    color=df_stats["avg_discount"],
                    colorscale=[
                        [0.0, "#FF9900"],
                        [0.5, "#FF5733"],
                        [1.0, "#e63946"],
                    ],
                    colorbar=dict(
                        title="Desc. %",
                        thickness=12,
                        len=0.6,
                    ),
                    line=dict(color="#0E1117", width=1.5),
                ),
                text=df_stats["total_revenue"].apply(lambda v: f"₹{v/1000:.0f}k"),
                textfont=dict(size=7, color="#0E1117"),
                textposition="middle center",
                customdata=df_stats[["avg_discount", "product_count", "total_revenue"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Faturamento: ₹ %{x:,.0f}<br>"
                    "Desconto médio: %{customdata[0]:.1f}%<br>"
                    "Produtos: %{customdata[1]}<extra></extra>"
                ),
                name="",
                showlegend=False,
            )
        )

        fig_lp.update_layout(
            **PLOTLY_LAYOUT,
            height=max(380, len(df_stats) * 26),
            xaxis=dict(
                title="Faturamento Total (₹)",
                tickformat=",.0f",
                gridcolor="#1e2130",
                zeroline=False,
            ),
            yaxis=dict(title="", tickfont=dict(size=11)),
        )
        st.plotly_chart(fig_lp, use_container_width=True)
    else:
        st.info("Sem dados para o Lollipop.")

    # Slider abaixo do gráfico
    st.slider("Top N categorias", 5, 30, _lp_n, key="lp_topn",
              help="Quantas categorias exibir")

with col_right:
    st.markdown('<p class="section-label">Top Produtos por Avaliações</p>', unsafe_allow_html=True)
    st.subheader("Top 10 Mais Avaliados")

    top10 = fetch_top10()
    if top10:
        df_t = pd.DataFrame(top10)
        df_t["short_name"]   = df_t["product_name"].str[:40] + "…"
        df_t["rating"]       = pd.to_numeric(df_t["rating"],       errors="coerce").fillna(0)
        df_t["rating_count"] = pd.to_numeric(df_t["rating_count"], errors="coerce").fillna(0)

        fig_bar = px.bar(
            df_t,
            x="rating_count",
            y="short_name",
            orientation="h",
            color="rating",
            color_continuous_scale=[[0, "#2d3143"], [0.5, AMAZON_ORANGE], [1, "#FF5733"]],
            text="rating_count",
            labels={"rating_count": "Nº Avaliações", "short_name": "Produto", "rating": "Rating"},
        )
        fig_bar.update_layout(**PLOTLY_LAYOUT, height=400,
                              yaxis={"categoryorder": "total ascending"},
                              coloraxis_colorbar=dict(title="Rating"))
        fig_bar.update_traces(textposition="outside")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Sem dados para o Top 10.")

st.divider()


# ─────────────────────────────────────────────────────────────
# Filtros inline — dentro da página (colapsável)
# ─────────────────────────────────────────────────────────────
with st.expander("🔍 Filtros de Busca", expanded=False):
    fi_col1, fi_col2, fi_col3, fi_col4 = st.columns([2, 2, 2, 1])

    with fi_col1:
        selected_category = st.selectbox(
            "Categoria",
            options=["(todas)"] + category_options,
            index=0,
            key="filter_category",
        )
    with fi_col2:
        price_range = st.slider(
            "Faixa de Preço (₹)",
            min_value=0, max_value=100_000,
            value=(0, 100_000), step=500,
            key="filter_price",
        )
    with fi_col3:
        min_rating_filter = st.slider(
            "Rating mínimo ★",
            min_value=0.0, max_value=5.0,
            value=0.0, step=0.5,
            key="filter_rating",
        )
    with fi_col4:
        st.markdown("<br/>", unsafe_allow_html=True)  # alinha verticalmente
        apply = st.button("🔍 Aplicar", type="primary", use_container_width=True)

    # Rótulo de estado
    active_filters = []
    if selected_category != "(todas)": active_filters.append(f"Categoria: **{selected_category[:30]}**")
    if price_range != (0, 100_000):    active_filters.append(f"Preço: ₹{price_range[0]:,}–₹{price_range[1]:,}")
    if min_rating_filter > 0:          active_filters.append(f"Rating ≥ {min_rating_filter}")
    if active_filters:
        st.caption("Filtros ativos: " + " · ".join(active_filters))
    else:
        st.caption("Nenhum filtro ativo — exibindo todos os dados.")


# ─────────────────────────────────────────────────────────────
# Linha 2: Boxplot + Word Frequency
# ─────────────────────────────────────────────────────────────
col_box, col_words = st.columns([3, 2], gap="medium")

with col_box:
    st.markdown('<p class="section-label">Distribuição de Preços</p>', unsafe_allow_html=True)
    st.subheader("Boxplot por Categoria")

    _bp_n = st.session_state.get("bp_topn", 8)
    price_data = fetch_price_distribution(top_n=_bp_n)
    if price_data:
        df_bp = pd.DataFrame(price_data)
        # Ordenar categorias pela mediana (Pareto visual)
        order = (
            df_bp.groupby("category")["discounted_price"]
            .median()
            .sort_values(ascending=False)
            .index.tolist()
        )
        fig_box = px.box(
            df_bp,
            x="category",
            y="discounted_price",
            category_orders={"category": order},
            color="category",
            color_discrete_sequence=px.colors.qualitative.Dark24,
            labels={"discounted_price": "Preço com Desconto (₹)", "category": ""},
            points=False,
        )
        fig_box.update_layout(
            **PLOTLY_LAYOUT,
            height=400,
            showlegend=False,
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_box, use_container_width=True)
        st.caption("Outliers ocultos. Passe o mouse para ver Q1, mediana e Q3.")
    else:
        st.info("Sem dados para o Boxplot.")

    # Slider abaixo do gráfico
    st.slider("Top N categorias", 3, 15, _bp_n, key="bp_topn",
              help="Quantas categorias exibir no boxplot")

with col_words:
    st.markdown('<p class="section-label">Análise de Reviews</p>', unsafe_allow_html=True)
    cat_for_words = selected_category if selected_category != "(todas)" else None
    st.subheader(f"Palavras Frequentes{f' · {cat_for_words[:20]}' if cat_for_words else ''}")

    _w_n = st.session_state.get("w_topn", 25)
    words = fetch_review_words(top_n=_w_n, category=cat_for_words)
    if words:
        df_w = pd.DataFrame(words)
        fig_w = px.bar(
            df_w.sort_values("count"),
            x="count",
            y="word",
            orientation="h",
            color="count",
            color_continuous_scale=[[0, "#2d3143"], [1, AMAZON_ORANGE]],
            labels={"count": "Frequência", "word": "Palavra"},
        )
        fig_w.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False,
                            coloraxis_showscale=False)
        st.plotly_chart(fig_w, use_container_width=True)
    else:
        st.info("Sem dados de reviews para esta seleção.")

    # Slider abaixo do gráfico
    st.slider("Top N palavras", 10, 50, _w_n, key="w_topn",
              help="Quantas palavras exibir")

st.divider()


# ─────────────────────────────────────────────────────────────
# Linha 3: Scatter (Desconto vs Rating) — com filtros ativos
# ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Correlação</p>', unsafe_allow_html=True)
st.subheader(" Desconto (%) vs Rating")

if selected_category != "(todas)":
    products_scatter = fetch_by_category(
        category=selected_category,
        min_price=price_range[0] if price_range[0] > 0 else None,
        max_price=price_range[1] if price_range[1] < 100_000 else None,
        min_rating=min_rating_filter if min_rating_filter > 0 else None,
    )
    if products_scatter:
        df_sc = pd.DataFrame(products_scatter)
        df_sc["discount_pct"]  = pd.to_numeric(df_sc.get("discount_pct"),  errors="coerce")
        df_sc["rating"]        = pd.to_numeric(df_sc.get("rating"),        errors="coerce")
        df_sc["rating_count"]  = pd.to_numeric(df_sc.get("rating_count"),  errors="coerce").fillna(1)
        df_sc = df_sc.dropna(subset=["discount_pct", "rating"])

        if not df_sc.empty:
            fig_sc = px.scatter(
                df_sc,
                x="discount_pct",
                y="rating",
                size="rating_count",
                size_max=45,
                color="rating",
                hover_name="product_name",
                color_continuous_scale=[[0, "#e63946"], [0.5, AMAZON_ORANGE], [1, "#2ecc71"]],
                labels={"discount_pct": "Desconto (%)", "rating": "Rating", "rating_count": "Nº Avaliações"},
            )
            fig_sc.update_layout(**PLOTLY_LAYOUT, height=400,
                                 coloraxis_colorbar=dict(title="Rating"))
            st.plotly_chart(fig_sc, use_container_width=True)
        else:
            st.info("Dados insuficientes para o scatter nesta seleção.")
    else:
        st.info("Nenhum produto encontrado com os filtros aplicados.")
else:
    st.info("🔍 Expanda o painel de filtros acima, selecione uma categoria e clique em Aplicar para ver a correlação.")

st.divider()


# ─────────────────────────────────────────────────────────────
# Galeria de Produtos (Cards)
# ─────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Galeria de Produtos</p>', unsafe_allow_html=True)
st.subheader("Cards de Produtos")

if selected_category != "(todas)":
    gallery_products = fetch_by_category(
        category=selected_category,
        min_price=price_range[0] if price_range[0] > 0 else None,
        max_price=price_range[1] if price_range[1] < 100_000 else None,
        min_rating=min_rating_filter if min_rating_filter > 0 else None,
    )

    if gallery_products:
        # Mostrar no máximo 20 cards (4 por linha)
        display = gallery_products[:20]
        cols = st.columns(4)
        for i, prod in enumerate(display):
            img   = prod.get("img_link")   or "https://via.placeholder.com/150?text=No+Image"
            name  = prod.get("product_name") or "Produto sem nome"
            link  = prod.get("product_link") or "#"
            price = prod.get("discounted_price")
            rating = prod.get("rating")

            price_str  = f"₹ {price:,.0f}" if price else "—"
            rating_str = f"⭐ {rating:.1f}" if rating else "⭐ —"

            with cols[i % 4]:
                st.markdown(f"""
                <div class="product-card">
                  <img src="{img}" alt="produto" onerror="this.src='https://via.placeholder.com/150?text=No+Image'"/>
                  <p class="p-name">{name[:90]}</p>
                  <p class="p-rating">{rating_str}</p>
                  <p class="p-price">{price_str}</p>
                  <a href="{link}" target="_blank">Ver na Amazon →</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Nenhum produto encontrado com os filtros aplicados.")
else:
    st.info("🔍 Expanda o painel de filtros acima e selecione uma categoria para ver a galeria.")

# ─── Footer ──────────────────────────────────────────────────
st.divider()
st.caption("Amazon Sales Dashboard · FastAPI + Streamlit + MySQL · 2026")
