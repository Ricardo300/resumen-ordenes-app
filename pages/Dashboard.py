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

# 🔎 Traer datos (sube el rango si tienes más de 20k)
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

# ✅ DataFrame
df = pd.DataFrame(data)

# ✅ Convertir fecha (obligatorio antes de usar .dt)
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
df = df.dropna(subset=["fecha"])

# ✅ Filtrar SOLO febrero 2026
df = df[(df["fecha"].dt.year == 2026) & (df["fecha"].dt.month == 2)]

if df.empty:
    st.warning("No hay datos para febrero 2026.")
    st.stop()

# ✅ Métricas
total_ordenes = df["orden_trabajo"].nunique()

df["garantia"] = df["garantia"].astype(str).str.upper()
total_garantias = df[df["garantia"] == "SI"]["orden_trabajo"].nunique()
porcentaje_garantia = (total_garantias / total_ordenes * 100) if total_ordenes else 0

# ✅ Hora promedio inicio (en minutos)
df["inicio"] = pd.to_datetime(df["inicio"], format="%H:%M:%S", errors="coerce")
df["inicio_minutos"] = df["inicio"].dt.hour * 60 + df["inicio"].dt.minute
hora_promedio_min = df["inicio_minutos"].mean()
hora_promedio_horas = round(hora_promedio_min / 60, 2) if pd.notnull(hora_promedio_min) else 0

# ✅ KPI cards
c1, c2, c3 = st.columns(3)
c1.metric("Total Órdenes (únicas)", total_ordenes)
c2.metric("% Garantías", f"{porcentaje_garantia:.2f}%")
c3.metric("Hora Promedio Inicio", f"{hora_promedio_horas} h")

st.divider()

# ✅ Gráfico BARRAS por día del mes
st.subheader("Órdenes por Provincia - Febrero 2026")

ordenes_provincia = (
    df.groupby("provincia")["orden_trabajo"]
    .nunique()
    .reset_index(name="total_ordenes")
    .sort_values("total_ordenes", ascending=False)
)

st.dataframe(ordenes_provincia, use_container_width=True)
