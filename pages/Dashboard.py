import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Dashboard KPI ETA - Febrero 2026")

# 🔐 Conexión
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# 🔎 Traer datos (hasta 20k registros)
response = (
    supabase
    .table("kpi_ordenes_completadas")
    .select("*")
    .range(0, 20000)
    .execute()
)

data = response.data

if not data:
    st.warning("No hay datos en la base.")
    st.stop()

df = pd.DataFrame(data)

# 🔧 Convertir fecha
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

# 🔥 Filtrar SOLO febrero 2026
df = df[
    (df["fecha"].dt.month == 2) &
    (df["fecha"].dt.year == 2026)
]

if df.empty:
    st.warning("No hay datos para febrero 2026.")
    st.stop()

# 🔢 MÉTRICAS

# Total órdenes únicas
total_ordenes = df["orden_trabajo"].nunique()

# % Garantías
df["garantia"] = df["garantia"].astype(str).str.upper()

total_garantias = df[df["garantia"] == "SI"]["orden_trabajo"].nunique()

porcentaje_garantia = (
    (total_garantias / total_ordenes) * 100
    if total_ordenes > 0 else 0
)

# 🕒 Hora promedio de inicio
df["inicio"] = pd.to_datetime(df["inicio"], format="%H:%M:%S", errors="coerce")

df["inicio_minutos"] = df["inicio"].dt.hour * 60 + df["inicio"].dt.minute

hora_promedio_min = df["inicio_minutos"].mean()

hora_promedio_horas = round(hora_promedio_min / 60, 2)

# 📊 Mostrar KPIs
col1, col2, col3 = st.columns(3)

col1.metric("Total Órdenes", total_ordenes)
col2.metric("% Garantías", f"{porcentaje_garantia:.2f}%")
col3.metric("Hora Promedio Inicio", f"{hora_promedio_horas} h")

st.divider()

# 📈 Órdenes por Día
ordenes_dia = (
    df.groupby("fecha")["orden_trabajo"]
    .nunique()
    .reset_index()
    .sort_values("fecha")
)

fig = px.line(
    ordenes_dia,
    x="fecha",
    y="orden_trabajo",
    markers=True,
    title="Órdenes por Día - Febrero 2026"
)

fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title="Cantidad",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)
