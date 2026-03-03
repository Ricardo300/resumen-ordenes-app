import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================
st.set_page_config(
    page_title="KPI ETA Febrero 2026",
    layout="wide"
)

# ==========================================
# CSS COMPACTO PROFESIONAL
# ==========================================
st.markdown("""
<style>

/* Reduce márgenes generales */
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 0rem;
}

/* Reduce espacio entre elementos */
div[data-testid="stVerticalBlock"] > div {
    gap: 0.5rem;
}

/* Métricas compactas */
div[data-testid="stMetric"] {
    background-color: #111827;
    padding: 8px 12px;
    border-radius: 8px;
}

div[data-testid="stMetricValue"] {
    font-size: 18px;
}

div[data-testid="stMetricLabel"] {
    font-size: 11px;
    color: #9ca3af;
}

/* Selectbox más pequeño */
div[data-baseweb="select"] {
    font-size: 13px;
}

/* Tablas más pequeñas */
[data-testid="stDataFrame"] div {
    font-size: 12px;
}

/* Quitar espacio extra debajo de títulos */
h3 {
    margin-bottom: 0.3rem;
}

</style>
""", unsafe_allow_html=True)

st.markdown("## 📊 Dashboard KPI ETA - Febrero 2026")

# ==========================================
# 🔐 CONEXIÓN SUPABASE
# ==========================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ==========================================
# FUNCIÓN CARGA DATOS
# ==========================================
@st.cache_data
def obtener_datos():
    todos = []
    limite = 1000
    inicio = 0

    while True:
        response = (
            supabase
            .table("kpi_ordenes_completadas")
            .select("*")
            .gte("fecha", "2026-02-01")
            .lt("fecha", "2026-03-01")
            .range(inicio, inicio + limite - 1)
            .execute()
        )

        data = response.data

        if not data:
            break

        todos.extend(data)

        if len(data) < limite:
            break

        inicio += limite

    return todos


data = obtener_datos()

if not data:
    st.warning("No hay datos para febrero 2026.")
    st.stop()

df = pd.DataFrame(data)
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

# ==========================================
# FILTROS COMPACTOS
# ==========================================
colf1, colf2, colf3 = st.columns([1,1,3])

with colf1:
    opciones_tecnologia = ["TODAS"] + sorted(df["tecnologia"].dropna().unique().tolist())
    tecnologia = st.selectbox("Tecnología", opciones_tecnologia)

with colf2:
    opciones_contrata = ["TODAS"] + sorted(df["contrata"].dropna().unique().tolist())
    contrata = st.selectbox("Contrata", opciones_contrata)

if tecnologia != "TODAS":
    df = df[df["tecnologia"] == tecnologia]

if contrata != "TODAS":
    df = df[df["contrata"] == contrata]

# ==========================================
# MÉTRICAS
# ==========================================
total_ordenes = len(df)
total_tecnicos = df["identificador_tecnico"].nunique()
dias_operativos = df["fecha"].nunique()
promedio_diario = round(total_ordenes / dias_operativos, 2) if dias_operativos > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Órdenes", f"{total_ordenes:,}")
col2.metric("Técnicos", total_tecnicos)
col3.metric("Días", dias_operativos)
col4.metric("Promedio Día", promedio_diario)

# ==========================================
# GRÁFICO COMPACTO
# ==========================================
df["dia_mes"] = df["fecha"].dt.day

ordenes_dia = (
    df.groupby("dia_mes")["orden_trabajo"]
    .nunique()
    .reset_index(name="ordenes")
    .sort_values("dia_mes")
)

fig = px.bar(
    ordenes_dia,
    x="dia_mes",
    y="ordenes",
    text="ordenes",
    color="ordenes",
    color_continuous_scale="Blues"
)

fig.update_layout(
    template="plotly_dark",
    height=280,
    margin=dict(l=10, r=10, t=10, b=10),
    coloraxis_showscale=False,
    xaxis_title="",
    yaxis_title=""
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TABLAS LADO A LADO
# ==========================================
col_tab1, col_tab2 = st.columns([1,2])

# -------------------------
# Provincia
# -------------------------
with col_tab1:
    st.markdown("### 📍 Provincia")

    ordenes_provincia = (
        df.groupby("provincia")["orden_trabajo"]
        .nunique()
        .reset_index(name="Órdenes")
        .sort_values("Órdenes", ascending=False)
    )

    st.dataframe(
        ordenes_provincia,
        use_container_width=True,
        height=260
    )

# -------------------------
# Producción Técnico
# -------------------------
with col_tab2:
    st.markdown("### 👷 Producción Técnico")

    df_prod = (
        df.groupby(["identificador_tecnico", "contrata"])
        .agg(
            Producción=("orden_trabajo", "count"),
            Dias_Trabajados=("fecha", "nunique")
        )
        .reset_index()
    )

    df_prod["Productividad"] = (
        df_prod["Producción"] / df_prod["Dias_Trabajados"]
    ).round(2)

    df_prod = df_prod.drop(columns=["Dias_Trabajados"])
    df_prod = df_prod.sort_values("Producción", ascending=False)

    st.dataframe(
        df_prod,
        use_container_width=True,
        height=260
    )
