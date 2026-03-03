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

# =============================
# 🔁 FUNCIÓN PARA TRAER TODO FEBRERO
# =============================

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
            .lt("fecha", "2026-03-01")  # 🔥 filtro correcto
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
# ============================================
# 🔎 FILTRO POR TECNOLOGÍA
# ============================================

opciones_tecnologia = ["TODAS"] + sorted(df["tecnologia"].dropna().unique().tolist())

tecnologia_seleccionada = st.selectbox(
    "Filtrar por Tecnología",
    opciones_tecnologia
)

if tecnologia_seleccionada != "TODAS":
    df = df[df["tecnologia"] == tecnologia_seleccionada]
# ============================================
# 🔎 FILTRO POR CONTRATA
# ============================================

opciones_contrata = ["TODAS"] + sorted(df["contrata"].dropna().unique().tolist())

contrata_seleccionada = st.selectbox(
    "Filtrar por Contrata",
    opciones_contrata
)

if contrata_seleccionada != "TODAS":
    df = df[df["contrata"] == contrata_seleccionada]
# ============================================
# 📊 RESUMEN GENERAL
# ============================================

st.subheader("Resumen General")

total_ordenes = len(df)
total_tecnicos = df["identificador_tecnico"].nunique()
dias_operativos = df["fecha"].nunique()

ordenes_promedio_por_dia = 0
if dias_operativos > 0:
    ordenes_promedio_por_dia = round(total_ordenes / dias_operativos, 2)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Órdenes", total_ordenes)
col2.metric("Técnicos Activos", total_tecnicos)
col3.metric("Días Operativos", dias_operativos)
col4.metric("Órdenes Promedio por Día", ordenes_promedio_por_dia)
# =============================
# 📋 TABLA POR PROVINCIA
# =============================

st.subheader("Órdenes por Provincia - Febrero 2026")

ordenes_provincia = (
    df.groupby("provincia")["orden_trabajo"]
    .nunique()
    .reset_index(name="total_ordenes")
    .sort_values("total_ordenes", ascending=False)
)

st.dataframe(ordenes_provincia, use_container_width=True)
# ============================================
# 📊 PRODUCCIÓN Y PRODUCTIVIDAD POR TÉCNICO
# ============================================

st.subheader("Producción y Productividad por Técnico")

df_prod = (
    df.groupby(["identificador_tecnico", "contrata"])
      .agg(
          produccion=("orden_trabajo", "count"),
          dias_trabajados=("fecha", "nunique")
      )
      .reset_index()
)

# Calcular productividad
df_prod["productividad"] = (
    df_prod["produccion"] / df_prod["dias_trabajados"]
).round(2)

# Eliminar columna dias_trabajados (solo se usa para cálculo)
df_prod = df_prod.drop(columns=["dias_trabajados"])

# Ordenar por producción
df_prod = df_prod.sort_values("produccion", ascending=False)

st.dataframe(df_prod, use_container_width=True)
# =============================
# 📊 GRÁFICO BARRAS POR DÍA
# =============================

df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
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
    title="Órdenes por Día - Febrero 2026"
)

fig.update_layout(
    template="plotly_dark",
    xaxis_title="Día del mes",
    yaxis_title="Cantidad de órdenes"
)

st.plotly_chart(fig, use_container_width=True)
