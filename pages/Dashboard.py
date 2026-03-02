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

# 🔎 Traer TODOS los registros (hasta 20k)
response = supabase.table("kpi_ordenes_completadas") \
    .select("*") \
    .range(0, 20000) \
    .execute()

data = response.data

if not data:
    st.warning("No hay datos en la base.")
    st.stop()

df = pd.DataFrame(data)

# 🔧 Convertir fecha correctamente
df["fecha"] = pd.to_datetime(df["fecha"])

# 🔥 FILTRAR SOLO FEBRERO 2026
df = df[
    (df["fecha"].dt.month == 2) &
    (df["fecha"].dt.year == 2026)
]

# 🔢 MÉTRICAS
total_ordenes = df["orden_trabajo"].nunique()

porcentaje_garantia = (
    df["garantia"].str.upper().eq("SI").sum() / total_ordenes * 100
    if total_ordenes > 0 else 0
)

hora_promedio = df["inicio"].mean()
hora_promedio_horas = round(hora_promedio.hour + hora_promedio.minute / 60, 2)

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
