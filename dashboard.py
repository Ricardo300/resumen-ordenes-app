import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

st.title("Dashboard KPI ETA - Febrero")

# 🔐 Conexión
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# 🔄 Traer datos
response = supabase.table("kpi_ordenes_completadas").select("*").execute()

data = response.data

if not data:
    st.warning("No hay datos en la base")
    st.stop()

df = pd.DataFrame(data)

# 🔄 Convertir fechas y horas
df["fecha"] = pd.to_datetime(df["fecha"])
df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce")

# 🔹 KPI 1: Total órdenes
total_ordenes = len(df)

# 🔹 KPI 2: % Garantías
porcentaje_garantia = (
    (df["garantia"].str.upper() == "SI").sum() / total_ordenes * 100
)

# 🔹 KPI 3: Promedio hora inicio
hora_promedio = df["inicio"].dt.hour.mean()

# 🔹 Mostrar KPIs
col1, col2, col3 = st.columns(3)

col1.metric("Total Órdenes", total_ordenes)
col2.metric("% Garantías", f"{porcentaje_garantia:.2f}%")
col3.metric("Hora Promedio Inicio", f"{hora_promedio:.2f} h")

st.divider()

# 🔹 Órdenes por día
ordenes_dia = df.groupby("fecha").size().reset_index(name="cantidad")

fig1 = px.line(
    ordenes_dia,
    x="fecha",
    y="cantidad",
    title="Órdenes por Día"
)

st.plotly_chart(fig1, use_container_width=True)

# 🔹 Órdenes por técnico
ordenes_tecnico = (
    df.groupby("identificador_tecnico")
    .size()
    .reset_index(name="cantidad")
    .sort_values("cantidad", ascending=False)
    .head(10)
)

fig2 = px.bar(
    ordenes_tecnico,
    x="identificador_tecnico",
    y="cantidad",
    title="Top 10 Técnicos por Producción"
)

st.plotly_chart(fig2, use_container_width=True)
