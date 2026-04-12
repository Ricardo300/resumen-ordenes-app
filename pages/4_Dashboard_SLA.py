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
# PREPARAR FECHA Y CAMPOS
# =====================================

df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
df = df[df["fecha"].notna()].copy()

if "fecha_asignacion" in df.columns:
    df["fecha_asignacion"] = pd.to_datetime(df["fecha_asignacion"], errors="coerce")

if "dilacion_dias" in df.columns:
    df["dilacion_dias"] = pd.to_numeric(df["dilacion_dias"], errors="coerce")

if "tipo_sla" in df.columns:
    df["tipo_sla"] = df["tipo_sla"].astype(str).str.strip()

if "comentario_bo" in df.columns:
    df["comentario_bo"] = df["comentario_bo"].astype(str).str.strip()

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

inst = df_filtrado[df_filtrado["tipo_sla"] == "Instalación"].copy()
rep = df_filtrado[df_filtrado["tipo_sla"] == "Reparación"].copy()

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
# GRAFICO COMENTARIO BO
# =====================================

df_comentario = df_filtrado.copy()

df_comentario = df_comentario[
    (
        (df_comentario["tipo_sla"] == "Reparación") &
        (df_comentario["dilacion_dias"] >= 2)
    )
    |
    (
        (df_comentario["tipo_sla"] != "Reparación") &
        (df_comentario["dilacion_dias"] >= 3)
    )
].copy()

if "comentario_bo" in df_comentario.columns:
    df_comentario = df_comentario[
        df_comentario["comentario_bo"].notna()
    ].copy()

    df_comentario["comentario_bo"] = df_comentario["comentario_bo"].astype(str).str.strip()

    df_comentario = df_comentario[
        (df_comentario["comentario_bo"] != "") &
        (df_comentario["comentario_bo"].str.upper() != "NONE") &
        (df_comentario["comentario_bo"].str.upper() != "NAN")
    ].copy()

if not df_comentario.empty:
    resumen_comentario = (
        df_comentario.groupby("comentario_bo")
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=True)
    )

    st.divider()
    st.subheader("Comentarios BO en órdenes con alta dilación")

    fig_comentario = px.bar(
        resumen_comentario,
        x="Cantidad",
        y="comentario_bo",
        orientation="h",
        text="Cantidad"
    )

    fig_comentario.update_traces(textposition="outside")
    fig_comentario.update_layout(
        height=max(400, len(resumen_comentario) * 45),
        xaxis_title="Cantidad",
        yaxis_title="",
        margin=dict(l=20, r=40, t=20, b=20)
    )

    st.plotly_chart(fig_comentario, use_container_width=True)

else:
    st.divider()
    st.subheader("Comentarios BO en órdenes con alta dilación")
    st.info("No hay registros con comentario_bo para los criterios seleccionados.")

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
