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

# =============================
# 🔢 MÉTRICAS
# =============================

# Total órdenes únicas
total_ordenes = df["orden_trabajo"].nunique()

# % Garantías
df["garantia"] = df["garantia"].astype(str).str.upper()
total_garantias = df[df["garantia"] == "SI"]["orden_trabajo"].nunique()

porcentaje_garantia = (
    (total_garantias / total_ordenes) * 100
    if total_ordenes > 0 else 0
)

# Hora promedio inicio
df["inicio"] = pd.to_datetime(df["inicio"], format="%H:%M:%S", errors="coerce")
df["inicio_minutos"] = df["inicio"].dt.hour * 60 + df["inicio"].dt.minute

hora_promedio_min = df["inicio_minutos"].mean()
hora_promedio_horas = round(hora_promedio_min / 60, 2) if pd.notnull(hora_promedio_min) else 0

# =============================
# 📊 KPI CARDS
# =============================

c1, c2, c3 = st.columns(3)
c1.metric("Total Órdenes (únicas)", total_ordenes)
c2.metric("% Garantías", f"{porcentaje_garantia:.2f}%")
c3.metric("Hora Promedio Inicio", f"{hora_promedio_horas} h")

st.divider()

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
