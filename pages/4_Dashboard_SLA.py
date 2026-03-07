import streamlit as st
from supabase import create_client
import pandas as pd

# =====================================
# CONFIGURACIÓN
# =====================================

st.set_page_config(
    page_title="Dashboard SLA",
    layout="wide"
)

st.title("Dilación desde creación hasta cierre")

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

datos = []
limite = 1000
inicio = 0

while True:

    response = (
        supabase
        .table("view_sla_operacion")
        .select("dilacion_dias,fecha,tipo_sla,tecnologia")
        .range(inicio, inicio + limite - 1)
        .execute()
    )

    data = response.data

    if not data:
        break

    datos.extend(data)
    inicio += limite

df = pd.DataFrame(datos)

# =====================================
# FILTRO FECHA (FEBRERO)
# =====================================

df["fecha"] = pd.to_datetime(df["fecha"])

df = df[
    (df["fecha"].dt.year == 2026) &
    (df["fecha"].dt.month == 2)
]

# =====================================
# FILTROS DASHBOARD
# =====================================

st.sidebar.title("Filtros")

tec = st.sidebar.selectbox(
    "Tecnología",
    ["Todas","GPON","DTH"]
)

sla = st.sidebar.selectbox(
    "Tipo SLA",
    ["Todos","INSTALACION","REPARACION"]
)

# =====================================
# APLICAR FILTROS
# =====================================

df_filtrado = df.copy()

if tec != "Todas":
    df_filtrado = df_filtrado[df_filtrado["tecnologia"] == tec]

if sla != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo_sla"] == sla]

# =====================================
# KPI
# =====================================

total_ordenes = len(df_filtrado)

inst = df_filtrado[df_filtrado["tipo_sla"] == "INSTALACION"]
rep = df_filtrado[df_filtrado["tipo_sla"] == "REPARACION"]

sla_inst = 0
sla_rep = 0

if len(inst) > 0:
    sla_inst = round(
        (len(inst[inst["dilacion_dias"] <= 3]) / len(inst)) * 100,
        2
    )

if len(rep) > 0:
    sla_rep = round(
        (len(rep[rep["dilacion_dias"] <= 2]) / len(rep)) * 100,
        2
    )

# =====================================
# MOSTRAR KPI
# =====================================

col1, col2, col3 = st.columns(3)

col1.metric("Total órdenes", total_ordenes)

col2.metric("SLA Instalaciones %", sla_inst)

col3.metric("SLA Reparaciones %", sla_rep)

st.divider()

# =====================================
# TABLA DILACIÓN
# =====================================

conteo = (
    df_filtrado.groupby("dilacion_dias")
    .size()
    .reset_index(name="Cantidad")
    .sort_values("dilacion_dias")
)

total = conteo["Cantidad"].sum()

conteo["Acumulado"] = conteo["Cantidad"].cumsum()

conteo["Febrero %"] = round((conteo["Acumulado"] / total) * 100, 2)

tabla_df = conteo.rename(columns={"dilacion_dias": "Dilación"})[
    ["Dilación", "Cantidad", "Febrero %"]
]

st.dataframe(
    tabla_df,
    use_container_width=True,
    hide_index=True
)
