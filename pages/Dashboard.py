import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
from datetime import datetime
import calendar

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================
st.set_page_config(
    page_title="Dashboard KPI ETA",
    layout="wide"
)

# ==========================================
# CSS COMPACTO PROFESIONAL
# ==========================================
st.markdown("""
<style>

/* Márgenes compactos */
.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
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

/* Tablas más pequeñas */
[data-testid="stDataFrame"] div {
    font-size: 12px;
}

/* Selectbox compacto */
div[data-baseweb="select"] {
    font-size: 13px;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard KPI ETA")

# ==========================================
# SELECTOR DE PERIODO (MES EN TEXTO)
# ==========================================
colp1, colp2 = st.columns(2)

with colp1:
    año = st.selectbox("Año", [2026, 2025, 2024], index=0)

with colp2:
    meses_dict = {
        "Enero": 1,
        "Febrero": 2,
        "Marzo": 3,
        "Abril": 4,
        "Mayo": 5,
        "Junio": 6,
        "Julio": 7,
        "Agosto": 8,
        "Septiembre": 9,
        "Octubre": 10,
        "Noviembre": 11,
        "Diciembre": 12
    }

    mes_nombre = st.selectbox(
        "Mes",
        list(meses_dict.keys()),
        index=datetime.now().month - 1
    )

    mes = meses_dict[mes_nombre]

primer_dia = f"{año}-{mes:02d}-01"
ultimo_dia_num = calendar.monthrange(año, mes)[1]
ultimo_dia = f"{año}-{mes:02d}-{ultimo_dia_num}"

st.markdown(f"**📅 Periodo Analizado:** {mes_nombre} {año}")

# ==========================================
# CONEXIÓN SUPABASE
# ==========================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ==========================================
# FUNCIÓN CARGA DATOS DINÁMICA
# ==========================================
@st.cache_data
def obtener_datos(primer_dia, ultimo_dia):
    todos = []
    limite = 1000
    inicio = 0

    while True:
        response = (
            supabase
            .table("kpi_ordenes_completadas")
            .select("*")
            .gte("fecha", primer_dia)
            .lte("fecha", ultimo_dia)
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


data = obtener_datos(primer_dia, ultimo_dia)

if not data:
    st.warning("No hay datos para el período seleccionado.")
    st.stop()

df = pd.DataFrame(data)
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

# ==========================================
# FILTROS
# ==========================================
colf1, colf2 = st.columns(2)

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
col3.metric("Días Operativos", dias_operativos)
col4.metric("Promedio Día", promedio_diario)

# ==========================================
# GRÁFICO ÓRDENES POR DÍA
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
col_tab1, col_tab2 = st.columns([1, 2])

# Provincia
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

# Producción Técnico
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
