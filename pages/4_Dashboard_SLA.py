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
        .select("*")
        .range(inicio, inicio + limite - 1)
        .execute()
    )

    data = response.data

    if not data:
        break

    datos.extend(data)
    inicio += limite

df = pd.DataFrame(datos)

if df.empty:
    st.warning("No se encontraron datos en view_sla_operacion.")
    st.stop()

# =====================================
# PREPARAR FECHA
# =====================================

df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
df = df[df["fecha"].notna()].copy()

df["anio"] = df["fecha"].dt.year
df["mes_num"] = df["fecha"].dt.month

meses_dict = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}

df["mes"] = df["mes_num"].map(meses_dict)

# =====================================
# FILTROS
# =====================================

st.sidebar.title("Filtros")

anios_disponibles = sorted(df["anio"].dropna().unique().tolist(), reverse=True)
anio = st.sidebar.selectbox("Año", anios_disponibles)

df_anio = df[df["anio"] == anio].copy()

meses_orden = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

meses_disponibles = [
    m for m in meses_orden
    if m in df_anio["mes"].dropna().unique().tolist()
]

mes = st.sidebar.selectbox("Mes", meses_disponibles)

df_mes = df_anio[df_anio["mes"] == mes].copy()

opciones_tec = ["Todas"] + sorted(
    df_mes["tecnologia"].dropna().astype(str).unique().tolist()
)

tec = st.sidebar.selectbox(
    "Tecnología",
    opciones_tec
)

opciones_sla = ["Todos"] + sorted(
    df_mes["tipo_sla"].dropna().astype(str).unique().tolist()
)

sla = st.sidebar.selectbox(
    "Tipo SLA",
    opciones_sla
)

# =====================================
# APLICAR FILTROS
# =====================================

df_filtrado = df_mes.copy()

if tec != "Todas":
    df_filtrado = df_filtrado[df_filtrado["tecnologia"].astype(str) == tec]

if sla != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo_sla"].astype(str) == sla]

# =====================================
# KPI
# =====================================

total_ordenes = df_filtrado["orden_trabajo"].nunique() if "orden_trabajo" in df_filtrado.columns else len(df_filtrado)

inst = df_filtrado[df_filtrado["tipo_sla"] == "INSTALACION"].copy()
rep = df_filtrado[df_filtrado["tipo_sla"] == "REPARACION"].copy()

sla_inst = 0
sla_rep = 0

if len(inst) > 0:
    sla_inst = round(
        (len(inst[inst["dilacion_dias"] <= 2]) / len(inst)) * 100,
        2
    )

if len(rep) > 0:
    sla_rep = round(
        (len(rep[rep["dilacion_dias"] <= 1]) / len(rep)) * 100,
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
# TABLA RESUMEN
# =====================================

conteo = (
    df_filtrado.groupby("dilacion_dias")
    .size()
    .reset_index(name="Cantidad")
    .sort_values("dilacion_dias")
)

total = conteo["Cantidad"].sum()

conteo["Acumulado"] = conteo["Cantidad"].cumsum()
conteo["% Acumulado"] = round((conteo["Acumulado"] / total) * 100, 2) if total > 0 else 0

tabla_df = conteo.rename(columns={"dilacion_dias": "Dilación"})[
    ["Dilación", "Cantidad", "% Acumulado"]
]

col_tabla = st.columns([1, 4, 1])

with col_tabla[1]:
    st.dataframe(
        tabla_df,
        use_container_width=True,
        hide_index=True
    )

# =====================================
# TABLA DEL VIEW FILTRADO
# =====================================

st.divider()
st.subheader("Detalle del view filtrado")

detalle_df = df_filtrado.copy()

if "orden_trabajo" in detalle_df.columns:
    detalle_df = detalle_df.sort_values(["fecha", "orden_trabajo"], ascending=[True, True])
else:
    detalle_df = detalle_df.sort_values("fecha", ascending=True)

st.dataframe(
    detalle_df,
    use_container_width=True,
    hide_index=True
)
