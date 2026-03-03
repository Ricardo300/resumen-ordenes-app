import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# ==========================================
# CONFIGURACIÓN VISUAL
# ==========================================
st.set_page_config(
    page_title="Dashboard KPI ETA",
    layout="wide"
)

# CSS para compactar y mejorar diseño
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-bottom: 0rem;
}

div[data-testid="stMetric"] {
    background-color: #111827;
    padding: 10px 15px;
    border-radius: 10px;
}

div[data-testid="stMetricValue"] {
    font-size: 22px;
}

div[data-testid="stMetricLabel"] {
    font-size: 12px;
    color: #9ca3af;
}

[data-testid="stDataFrame"] {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard KPI ETA - Febrero 2026")

# ==========================================
# 🔐 CONEXIÓN SUPABASE
# ==========================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ==========================================
# FUNCIÓN PARA TRAER DATOS
# ==========================================
@st.cache_data
def obtener_datos_febrero():
    todos_los_datos = []
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

        todos_los_datos.extend(data)

        if len(data) < limite:
            break

        inicio += limite

    return todos_los_datos


data = obtener_datos_febrero()

if not data:
    st.warning("No hay datos para febrero 2026.")
    st.stop()

df = pd.DataFrame(data)
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

# ==========================================
# 🔎 FILTROS HORIZONTALES
# ==========================================
st.markdown("### 🔎 Filtros")

col_f1, col_f2 = st.columns(2)

with col_f1:
    opciones_tecnologia = ["TODAS"] + sorted(df["tecnologia"].dropna().unique().tolist())
    tecnologia_seleccionada = st.selectbox("Tecnología", opciones_tecnologia)

with col_f2:
    opciones_contrata = ["TODAS"] + sorted(df["contrata"].dropna().unique().tolist())
    contrata_seleccionada = st.selectbox("Contrata", opciones_contrata)

if tecnologia_seleccionada != "TODAS":
    df = df[df["tecnologia"] == tecnologia_seleccionada]

if contrata_seleccionada != "TODAS":
    df = df[df["contrata"] == contrata_seleccionada]

# ==========================================
# 📊 RESUMEN GENERAL
# ==========================================
st.markdown("### 📈 Resumen General")

total_ordenes = len(df)
total_tecnicos = df["identificador_tecnico"].nunique()
dias_operativos = df["fecha"].nunique()

ordenes_promedio_por_dia = round(total_ordenes / dias_operativos, 2) if dias_operativos > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Órdenes", f"{total_ordenes:,}")
col2.metric("Técnicos Activos", total_tecnicos)
col3.metric("Días Operativos", dias_operativos)
col4.metric("Promedio Diario", ordenes_promedio_por_dia)

st.markdown("---")

# ==========================================
# 📊 GRÁFICO ÓRDENES POR DÍA
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
    height=350,
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis_title="Día del Mes",
    yaxis_title="Órdenes",
    coloraxis_showscale=False
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# 📋 ÓRDENES POR PROVINCIA
# ==========================================
st.markdown("### 📍 Órdenes por Provincia")

ordenes_provincia = (
    df.groupby("provincia")["orden_trabajo"]
    .nunique()
    .reset_index(name="Total Órdenes")
    .sort_values("Total Órdenes", ascending=False)
)

st.dataframe(ordenes_provincia, use_container_width=True, height=300)

st.markdown("---")

# ==========================================
# 📊 PRODUCCIÓN Y PRODUCTIVIDAD POR TÉCNICO
# ==========================================
st.markdown("### 👷 Producción y Productividad por Técnico")

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

st.dataframe(df_prod, use_container_width=True, height=400)
