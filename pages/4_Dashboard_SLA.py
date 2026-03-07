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

# =====================================
# ESTILOS VISUALES
# =====================================

st.markdown("""
<style>

[data-testid="stMetricValue"]{
font-size:38px;
font-weight:700;
}

[data-testid="stMetricLabel"]{
font-size:15px;
}

.block-container{
padding-top:2rem;
max-width:1100px;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# TITULO
# =====================================

st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
<span style="font-size:30px;">📊</span>
<h2 style="margin:0;font-weight:600;">
DILACIÓN DE ASIGNACIÓN
</h2>
</div>
""", unsafe_allow_html=True)

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
# FILTRO FEBRERO
# =====================================

df["fecha"] = pd.to_datetime(df["fecha"])

df = df[
    (df["fecha"].dt.year == 2026) &
    (df["fecha"].dt.month == 2)
]

# =====================================
# FILTROS
# =====================================

st.sidebar.title("Filtros")

opciones_tec = ["Todas"] + sorted(df["tecnologia"].dropna().unique().tolist())

tec = st.sidebar.selectbox(
    "Tecnología",
    opciones_tec
)

opciones_sla = ["Todos"] + sorted(df["tipo_sla"].dropna().unique().tolist())

sla = st.sidebar.selectbox(
    "Tipo SLA",
    opciones_sla
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
# KPIs
# =====================================

col1, col2, col3 = st.columns(3)

col1.metric("📦 Total órdenes", total_ordenes)

col2.metric("🛠 SLA Instalaciones %", sla_inst)

col3.metric("🔧 SLA Reparaciones %", sla_rep)

st.divider()

# =====================================
# TABLA
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

# centrar tabla
col_tabla = st.columns([1,4,1])

with col_tabla[1]:
    st.dataframe(
        tabla_df,
        use_container_width=True,
        hide_index=True
    )
