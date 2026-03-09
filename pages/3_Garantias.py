import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# =====================================
# CONFIGURACIÓN GENERAL
# =====================================

st.set_page_config(
    page_title="Dashboard Garantías",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================
# ESTILOS VISUALES
# =====================================

st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        padding-left: 1.2rem;
        padding-right: 1.2rem;
        max-width: 100%;
    }

    h1, h2, h3 {
        letter-spacing: -0.3px;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        font-size: 0.95rem;
        color: #9aa4b2;
        margin-bottom: 1.2rem;
    }

    .section-card {
        background-color: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 0.8rem 1rem 0.7rem 1rem;
        margin-bottom: 0.8rem;
    }

    .kpi-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.015) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 0.85rem 1rem;
        min-height: 110px;
    }

    .kpi-label {
        font-size: 0.92rem;
        color: #9aa4b2;
        margin-bottom: 0.45rem;
        font-weight: 500;
    }

    .kpi-value {
        font-size: 2.05rem;
        font-weight: 700;
        line-height: 1.1;
    }

    .small-note {
        color: #9aa4b2;
        font-size: 0.82rem;
        margin-top: 0.2rem;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        overflow: hidden;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }

    div[data-testid="stExpander"] {
        border-radius: 12px;
        overflow: hidden;
    }

    /* TABLA COMPACTA PROFESIONAL */
    .compact-table-container {
        max-height: 420px;
        overflow-y: auto;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
    }

    .compact-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }

    .compact-table thead th {
        position: sticky;
        top: 0;
        background: #161b26;
        padding: 6px 10px;
        text-align: left;
        border-bottom: 1px solid rgba(255,255,255,0.10);
        z-index: 1;
    }

    .compact-table tbody td {
        padding: 5px 10px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }

    .compact-table tbody tr:hover {
        background-color: rgba(255,255,255,0.03);
    }

    .compact-table .num {
        text-align: right;
        font-weight: 600;
        color: #8ab4ff;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Dashboard de Garantías</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Análisis de garantías, clasificación, técnicos, contratas y códigos de cierre.</div>',
    unsafe_allow_html=True
)

# =====================================
# CONEXIÓN SUPABASE
# =====================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =====================================
# FUNCIONES DE CARGA
# =====================================

@st.cache_data(ttl=600)
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

    return pd.DataFrame(todos)


@st.cache_data(ttl=600)
def cargar_servicios():
    todos = []
    limite = 1000
    inicio = 0

    while True:
        response = (
            supabase
            .table("kpi_ordenes_completadas")
            .select("fecha")
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

    df_local = pd.DataFrame(todos)

    if df_local.empty:
        df_local = pd.DataFrame(columns=["fecha", "anio", "mes_num"])
        return df_local

    df_local["fecha"] = pd.to_datetime(df_local["fecha"], errors="coerce")
    df_local["anio"] = df_local["fecha"].dt.year
    df_local["mes_num"] = df_local["fecha"].dt.month

    return df_local


# =====================================
# CARGA DE DATOS
# =====================================

df = cargar_garantias()
df_servicios = cargar_servicios()

# =====================================
# LIMPIEZA DE DATOS
# =====================================

if df.empty:
    st.warning("No se encontraron datos en vista_garantias.")
    st.stop()

df["fecha_garantia"] = pd.to_datetime(df["fecha_garantia"], errors="coerce")
df["contrata_causa_garantia"] = df["contrata_causa_garantia"].fillna("SIN CONTRATA")
df["tipo_garantia"] = df["tipo_garantia"].fillna("SIN CLASIFICAR")
df["clasificacion_garantia"] = df["clasificacion_garantia"].fillna("SIN CLASIFICAR")
df["tecnico_causa_garantia"] = df["tecnico_causa_garantia"].fillna("SIN TECNICO")
df["codigo_completado"] = df["codigo_completado"].fillna("SIN CODIGO")
df["rango_garantia"] = df["rango_garantia"].fillna("SIN RANGO")

if "tecnologia" not in df.columns:
    df["tecnologia"] = "DESCONOCIDA"
else:
    df["tecnologia"] = df["tecnologia"].fillna("SIN TECNOLOGIA")

if "dias_desde_visita" not in df.columns:
    df["dias_desde_visita"] = 0

df["anio"] = df["fecha_garantia"].dt.year
df["mes_num"] = df["fecha_garantia"].dt.month

# =====================================
# FILTROS
# =====================================

st.sidebar.header("Filtros")

anios = sorted([x for x in df["anio"].dropna().unique()])
if not anios:
    st.warning("No hay años disponibles en los datos.")
    st.stop()

anio_filtro = st.sidebar.selectbox(
    "Año",
    anios,
    index=len(anios) - 1
)

meses = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

mes_num = st.sidebar.selectbox(
    "Mes",
    list(meses.keys()),
    format_func=lambda x: meses[x]
)

def filtro_checkbox(label, opciones, key_prefix):
    with st.sidebar.expander(label, expanded=False):
        col1, col2 = st.columns(2)

        if col1.button("✓ Todo", key=f"{key_prefix}_all"):
            for opcion in opciones:
                st.session_state[f"{key_prefix}_{opcion}"] = True

        if col2.button("✕ Ninguno", key=f"{key_prefix}_none"):
            for opcion in opciones:
                st.session_state[f"{key_prefix}_{opcion}"] = False

        seleccionados = []

        for opcion in opciones:
            estado_key = f"{key_prefix}_{opcion}"
            if estado_key not in st.session_state:
                st.session_state[estado_key] = True

            estado = st.checkbox(opcion, key=estado_key)
            if estado:
                seleccionados.append(opcion)

    return seleccionados

opciones_contrata = sorted(df["contrata_causa_garantia"].unique())
opciones_tecnologia = sorted(df["tecnologia"].unique())
opciones_tipo = sorted(df["tipo_garantia"].unique())

contrata = filtro_checkbox("Contrata", opciones_contrata, "con")
tecnologia = filtro_checkbox("Tecnología", opciones_tecnologia, "tec")
tipo_garantia = filtro_checkbox("Tipo Garantía", opciones_tipo, "tip")

# =====================================
# APLICAR FILTROS
# =====================================

df_filtrado = df[
    (df["anio"] == anio_filtro) &
    (df["mes_num"] == mes_num) &
    (df["contrata_causa_garantia"].isin(contrata)) &
    (df["tecnologia"].isin(tecnologia)) &
    (df["tipo_garantia"].isin(tipo_garantia))
].copy()

servicios_mes = df_servicios[
    (df_servicios["anio"] == anio_filtro) &
    (df_servicios["mes_num"] == mes_num)
].copy()

total_servicios = len(servicios_mes)

# =====================================
# KPIs
# =====================================

total_garantias = len(df_filtrado)

garantias_internas = len(df_filtrado[df_filtrado["tipo_garantia"] == "INTERNA"])
garantias_externas = len(df_filtrado[df_filtrado["tipo_garantia"] == "EXTERNA"])
garantias_tecnico_kpi = len(df_filtrado[df_filtrado["clasificacion_garantia"] == "TECNICO"])

if total_servicios > 0:
    pct_garantia_interna = round((garantias_internas / total_servicios) * 100, 2)
    pct_garantia_tecnico = round((garantias_tecnico_kpi / total_servicios) * 100, 2)
else:
    pct_garantia_interna = 0
    pct_garantia_tecnico = 0

def render_kpi(label, value, note=""):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="small-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    render_kpi("Total Garantías", f"{total_garantias:,}", "Garantías filtradas")
with k2:
    render_kpi("Garantías Internas", f"{garantias_internas:,}", "Causadas por orden anterior")
with k3:
    render_kpi("Garantías Externas", f"{garantias_externas:,}", "Sin orden causal")
with k4:
    render_kpi("% Garantía Interna", f"{pct_garantia_interna}%", f"Sobre {total_servicios:,} servicios")
with k5:
    render_kpi("% Garantía Técnico", f"{pct_garantia_tecnico}%", f"Clasificación técnico / {total_servicios:,}")

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# =====================================
# HELPERS
# =====================================

def estilo_fig(fig, titulo_x="", titulo_y="", altura=380):
    fig.update_layout(
        template="plotly_dark",
        height=altura,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
        xaxis_title=titulo_x,
        yaxis_title=titulo_y,
        legend_title_text="",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.10)")
    return fig

def tabla_compacta(df_tabla):
    headers = "".join([f"<th>{col}</th>" for col in df_tabla.columns])

    filas = []
    for _, row in df_tabla.iterrows():
        celdas = []
        for col in df_tabla.columns:
            valor = row[col]
            if col == "Garantías":
                celdas.append(f'<td class="num">{valor}</td>')
            else:
                celdas.append(f"<td>{valor}</td>")
        filas.append(f"<tr>{''.join(celdas)}</tr>")

    html = f"""
    <div class="compact-table-container">
        <table class="compact-table">
            <thead>
                <tr>{headers}</tr>
            </thead>
            <tbody>
                {''.join(filas)}
            </tbody>
        </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)

# =====================================
# PRIMERA FILA DE GRÁFICOS
# =====================================

col_g1, col_g2 = st.columns([1.05, 0.95])

with col_g1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Clasificación de Garantías")

    clasificacion_df = (
        df_filtrado
        .groupby("clasificacion_garantia")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )

    fig_clasificacion = px.bar(
        clasificacion_df,
        x="clasificacion_garantia",
        y="cantidad",
        text="cantidad"
    )
    fig_clasificacion.update_traces(textposition="outside")
    fig_clasificacion = estilo_fig(fig_clasificacion, "Clasificación", "Cantidad", 360)

    st.plotly_chart(fig_clasificacion, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_g2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Garantías por Rango de Días")

    garantias_rango = (
        df_filtrado
        .groupby("rango_garantia")
        .size()
        .reset_index(name="cantidad")
    )

    orden = ["0-7", "8-15", "16-30", "31-60", "61-90", ">90", "SIN RANGO"]

    garantias_rango["rango_garantia"] = pd.Categorical(
        garantias_rango["rango_garantia"],
        categories=orden,
        ordered=True
    )

    garantias_rango = garantias_rango.sort_values("rango_garantia")

    fig_rango = px.bar(
        garantias_rango,
        x="rango_garantia",
        y="cantidad",
        text="cantidad"
    )
    fig_rango.update_traces(textposition="outside")
    fig_rango = estilo_fig(fig_rango, "Rango", "Cantidad", 360)

    st.plotly_chart(fig_rango, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# SEGUNDA FILA
# =====================================

col_g3, col_g4 = st.columns([1.1, 0.9])

# with col_g3:
#     st.markdown('<div class="section-card">', unsafe_allow_html=True)
#     st.subheader("Garantías por Contrata")

#     garantias_contrata = (
#         df_filtrado
#         .groupby("contrata_causa_garantia")
#         .size()
#         .reset_index(name="cantidad")
#         .sort_values("cantidad", ascending=False)
#     )

#     fig_contrata = px.bar(
#         garantias_contrata,
#         x="contrata_causa_garantia",
#         y="cantidad",
#         text="cantidad"
#     )
#     fig_contrata.update_traces(textposition="outside")
#     fig_contrata = estilo_fig(fig_contrata, "Contrata", "Cantidad", 390)
#     fig_contrata.update_xaxes(tickangle=-35)

#     st.plotly_chart(fig_contrata, use_container_width=True)
#     st.markdown('</div>', unsafe_allow_html=True)

with col_g4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Top 15 Códigos de Cierre")

    codigos_cierre = (
        df_filtrado
        .groupby("codigo_completado")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
        .head(15)
    )

    fig_codigos = px.bar(
        codigos_cierre.sort_values("cantidad", ascending=True),
        x="cantidad",
        y="codigo_completado",
        orientation="h",
        text="cantidad"
    )
    fig_codigos.update_traces(textposition="outside")
    fig_codigos = estilo_fig(fig_codigos, "Cantidad", "Código", 390)

    st.plotly_chart(fig_codigos, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# TABLAS
# =====================================

t1, t2 = st.columns([1.05, 0.95])

with t1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Garantías por Técnico")

    garantias_tecnico = (
        df_filtrado
        .groupby(["tecnico_causa_garantia", "contrata_causa_garantia"])
        .size()
        .reset_index(name="garantias")
        .sort_values(["garantias", "tecnico_causa_garantia"], ascending=[False, True])
    )

    garantias_tecnico = garantias_tecnico.rename(columns={
        "tecnico_causa_garantia": "Técnico",
        "contrata_causa_garantia": "Contrata",
        "garantias": "Garantías"
    })

    garantias_tecnico = garantias_tecnico.drop(columns=["Contrata"])

    tabla_compacta(garantias_tecnico)
    st.markdown('</div>', unsafe_allow_html=True)

with t2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Top 15 Códigos de Cierre")

    codigos_cierre_tabla = (
        df_filtrado
        .groupby("codigo_completado")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
        .head(15)
        .rename(columns={
            "codigo_completado": "Código de Cierre",
            "cantidad": "Garantías"
        })
    )

    st.dataframe(
        codigos_cierre_tabla,
        use_container_width=True,
        hide_index=True,
        height=420,
        row_height=26
    )
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# DETALLE FINAL
# =====================================

with st.expander("Ver detalle de garantías filtradas", expanded=False):
    columnas_detalle = [
        c for c in [
            "orden_trabajo",
            "numero_cliente",
            "fecha_garantia",
            "sub_tipo_orden",
            "tipo_actividad",
            "tecnologia",
            "tecnico_causa_garantia",
            "contrata_causa_garantia",
            "codigo_completado",
            "clasificacion_garantia",
            "tipo_garantia",
            "rango_garantia",
            "dias_desde_visita"
        ] if c in df_filtrado.columns
    ]

    st.dataframe(
        df_filtrado[columnas_detalle],
        use_container_width=True,
        hide_index=True,
        height=420,
        row_height=26
    )
