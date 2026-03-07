import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# =====================================
# CONFIGURACIÓN
# =====================================

st.set_page_config(
    page_title="Dashboard SLA",
    layout="wide"
)

st.title("Dashboard SLA Operación")

# =====================================
# CONEXIÓN SUPABASE
# =====================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =====================================
# CARGAR DATOS
# =====================================

response = supabase.table("view_sla_operacion").select("*").execute()

df = pd.DataFrame(response.data)

# =====================================
# FILTRO
# =====================================

st.sidebar.header("Filtros")

tipo_sla = st.sidebar.selectbox(
    "Tipo SLA",
    sorted(df["tipo_sla"].unique())
)

df = df[df["tipo_sla"] == tipo_sla]

# =====================================
# KPIs
# =====================================

col1, col2, col3 = st.columns(3)

total_ordenes = len(df)

promedio_dilacion = round(df["dilacion_dias"].mean(),2)

# regla SLA según tipo
if tipo_sla == "INSTALACION":
    limite = 3
elif tipo_sla == "REPARACION":
    limite = 2
else:
    limite = 3

sla = (df[df["dilacion_dias"] <= limite].shape[0] / total_ordenes) * 100

col1.metric(
    "Total Órdenes",
    total_ordenes
)

col2.metric(
    "Promedio Dilación",
    promedio_dilacion
)

col3.metric(
    "SLA %",
    round(sla,2)
)

st.divider()

# =====================================
# DISTRIBUCIÓN DÍAS
# =====================================

dist = df.groupby("dilacion_dias").size().reset_index(name="cantidad")

fig = px.bar(
    dist,
    x="dilacion_dias",
    y="cantidad",
    title="Distribución de Días de Dilación",
    text="cantidad"
)

st.plotly_chart(fig, use_container_width=True)

# =====================================
# ÓRDENES POR CONTRATA
# =====================================

contrata = df.groupby("contrata").size().reset_index(name="ordenes")

fig2 = px.bar(
    contrata,
    x="contrata",
    y="ordenes",
    title="Órdenes por Contrata",
    text="ordenes"
)

st.plotly_chart(fig2, use_container_width=True)
