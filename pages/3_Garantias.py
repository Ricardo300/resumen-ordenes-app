import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# =====================================
# CONFIGURACIÓN
# =====================================

st.set_page_config(page_title="Dashboard Garantías", layout="wide")

st.title("Dashboard de Garantías")

# =====================================
# CONEXIÓN SUPABASE
# =====================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =====================================
# FUNCIÓN PARA CARGAR DATOS
# =====================================

@st.cache_data
def cargar_garantias():

    todos = []
    limite = 1000
    inicio = 0

    while True:

        response = (
            supabase
            .table("vista_garantias")
            .select("*")
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

    df = pd.DataFrame(todos)

    return df


# =====================================
# CARGAR DATOS
# =====================================

df = cargar_garantias()

# =====================================
# KPIs
# =====================================

col1, col2, col3, col4 = st.columns(4)

total = len(df)

internas = len(df[df["tipo_garantia"] == "INTERNA"])

externas = len(df[df["tipo_garantia"] == "EXTERNA"])

promedio_dias = round(df["dias_desde_visita"].mean(), 1)

col1.metric("Total Garantías", total)

col2.metric("Garantías Internas", internas)

col3.metric("Garantías Externas", externas)

col4.metric("Promedio días garantía", promedio_dias)

# =====================================
# GARANTÍAS POR CONTRATA
# =====================================

st.subheader("Garantías por Contrata")

garantias_contrata = (
    df.groupby("contrata_causa_garantia")
    .size()
    .reset_index(name="cantidad")
    .sort_values("cantidad", ascending=False)
)

fig = px.bar(
    garantias_contrata,
    x="contrata_causa_garantia",
    y="cantidad",
    text="cantidad"
)

fig.update_layout(
    xaxis_title="Contrata",
    yaxis_title="Cantidad de Garantías"
)

st.plotly_chart(fig, use_container_width=True)
# =====================================
# GARANTÍAS POR TÉCNICO
# =====================================

st.subheader("Garantías por Técnico")

garantias_tecnico = (
    df.groupby("tecnico_causa_garantia")
    .size()
    .reset_index(name="cantidad")
    .sort_values("cantidad", ascending=False)
)

# opcional: mostrar solo los 20 técnicos con más garantías
garantias_tecnico = garantias_tecnico.head(20)

fig_tecnico = px.bar(
    garantias_tecnico,
    x="tecnico_causa_garantia",
    y="cantidad",
    text="cantidad"
)

fig_tecnico.update_layout(
    xaxis_title="Técnico",
    yaxis_title="Cantidad de Garantías"
)

st.plotly_chart(fig_tecnico, use_container_width=True)
# =====================================
# GARANTÍAS POR RANGO DE DÍAS
# =====================================

st.subheader("Garantías por Rango de Días")

garantias_rango = (
    df.groupby("rango_garantia")
    .size()
    .reset_index(name="cantidad")
)

# ordenar rangos correctamente
orden_rangos = ["0-7","8-15","16-30","31-60","61-90",">90"]

garantias_rango["rango_garantia"] = pd.Categorical(
    garantias_rango["rango_garantia"],
    categories=orden_rangos,
    ordered=True
)

garantias_rango = garantias_rango.sort_values("rango_garantia")

fig_rango = px.bar(
    garantias_rango,
    x="rango_garantia",
    y="cantidad",
    text="cantidad"
)

fig_rango.update_layout(
    xaxis_title="Rango de días",
    yaxis_title="Cantidad de Garantías"
)

st.plotly_chart(fig_rango, use_container_width=True)
# =====================================
# TABLA
# =====================================

st.subheader("Detalle de Garantías")

st.dataframe(df, use_container_width=True)
