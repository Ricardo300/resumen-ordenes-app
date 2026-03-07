import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# =====================================
# CONFIGURACIÓN
# =====================================

st.set_page_config(
    page_title="Dashboard Garantías",
    layout="wide"
)

# =====================================
# PALETA DE COLORES
# =====================================

COLOR_AZUL_OSCURO = "rgba(0,92,187,0.7)"
COLOR_AZUL_CLARO = "rgba(64,156,255,0.7)"

# =====================================
# ESTILOS VISUALES
# =====================================

st.markdown("""
<style>

.block-container{
padding-top:1.2rem;
padding-bottom:1rem;
padding-left:1.2rem;
padding-right:1.2rem;
max-width:100%;
}

.main-title{
font-size:2.6rem;
font-weight:700;
margin-bottom:0.4rem;
padding-top:0.3rem;
line-height:1.2;
}

.subtitle{
font-size:0.95rem;
color:#9aa4b2;
margin-bottom:1.2rem;
}

.section-card{
background-color:rgba(255,255,255,0.02);
border:1px solid rgba(255,255,255,0.08);
border-radius:14px;
padding:0.8rem 1rem;
margin-bottom:0.8rem;
}

.kpi-card{
background:linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.015) 100%);
border:1px solid rgba(255,255,255,0.08);
border-radius:14px;
padding:0.8rem 1rem;
}

.kpi-label{
font-size:0.9rem;
color:#9aa4b2;
margin-bottom:0.4rem;
}

.kpi-value{
font-size:2rem;
font-weight:700;
}

</style>
""", unsafe_allow_html=True)

# =====================================
# TITULO
# =====================================

st.markdown(
'<div class="main-title">📊 Dashboard de Garantías</div>',
unsafe_allow_html=True
)

st.markdown(
'<div class="subtitle">Análisis de garantías, técnicos, contratas y códigos de cierre.</div>',
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
# CARGAR DATOS
# =====================================

@st.cache_data
def cargar_garantias():

    todos=[]
    limite=1000
    inicio=0

    while True:

        response=(
        supabase
        .table("vista_garantias")
        .select("*")
        .range(inicio,inicio+limite-1)
        .execute()
        )

        data=response.data

        if not data:
            break

        todos.extend(data)

        if len(data)<limite:
            break

        inicio+=limite

    return pd.DataFrame(todos)


@st.cache_data
def cargar_servicios():

    todos=[]
    limite=1000
    inicio=0

    while True:

        response=(
        supabase
        .table("kpi_ordenes_completadas")
        .select("fecha")
        .range(inicio,inicio+limite-1)
        .execute()
        )

        data=response.data

        if not data:
            break

        todos.extend(data)

        if len(data)<limite:
            break

        inicio+=limite

    df=pd.DataFrame(todos)

    df["fecha"]=pd.to_datetime(df["fecha"],errors="coerce")
    df["anio"]=df["fecha"].dt.year
    df["mes"]=df["fecha"].dt.month

    return df


df=cargar_garantias()
df_servicios=cargar_servicios()

# =====================================
# LIMPIEZA
# =====================================

df["fecha_garantia"]=pd.to_datetime(df["fecha_garantia"],errors="coerce")

df["anio"]=df["fecha_garantia"].dt.year
df["mes"]=df["fecha_garantia"].dt.month

df["contrata_causa_garantia"]=df["contrata_causa_garantia"].fillna("SIN CONTRATA")
df["clasificacion_garantia"]=df["clasificacion_garantia"].fillna("SIN CLASIFICAR")
df["tecnico_causa_garantia"]=df["tecnico_causa_garantia"].fillna("SIN TECNICO")
df["codigo_completado"]=df["codigo_completado"].fillna("SIN CODIGO")
df["rango_garantia"]=df["rango_garantia"].fillna("SIN RANGO")

# =====================================
# FILTROS
# =====================================

st.sidebar.header("Filtros")

anios=sorted(df["anio"].dropna().unique())

anio_filtro=st.sidebar.selectbox("Año",anios)

mes_filtro=st.sidebar.selectbox(
"Mes",
[1,2,3,4,5,6,7,8,9,10,11,12]
)

df_filtrado=df[
(df["anio"]==anio_filtro)&
(df["mes"]==mes_filtro)
]

servicios_mes=df_servicios[
(df_servicios["anio"]==anio_filtro)&
(df_servicios["mes"]==mes_filtro)
]

# =====================================
# KPIs
# =====================================

total_garantias=len(df_filtrado)

garantias_internas=len(
df_filtrado[df_filtrado["tipo_garantia"]=="INTERNA"]
)

garantias_externas=len(
df_filtrado[df_filtrado["tipo_garantia"]=="EXTERNA"]
)

garantias_tecnico=len(
df_filtrado[df_filtrado["clasificacion_garantia"]=="TECNICO"]
)

total_servicios=len(servicios_mes)

pct_garantia_interna=round((garantias_internas/total_servicios)*100,2) if total_servicios>0 else 0
pct_garantia_tecnico=round((garantias_tecnico/total_servicios)*100,2) if total_servicios>0 else 0

col1,col2,col3,col4,col5=st.columns(5)

with col1:
    st.metric("Total Garantías",total_garantias)

with col2:
    st.metric("Garantías Internas",garantias_internas)

with col3:
    st.metric("Garantías Externas",garantias_externas)

with col4:
    st.metric("% Garantía Interna",f"{pct_garantia_interna}%")

with col5:
    st.metric("% Garantía Técnico",f"{pct_garantia_tecnico}%")

# =====================================
# GRAFICOS
# =====================================

col1,col2=st.columns(2)

with col1:

    st.subheader("📌 Clasificación de Garantías")

    clasificacion_df=(
    df_filtrado
    .groupby("clasificacion_garantia")
    .size()
    .reset_index(name="cantidad")
    )

    fig=px.bar(
    clasificacion_df,
    x="clasificacion_garantia",
    y="cantidad",
    text="cantidad",
    color_discrete_sequence=[COLOR_AZUL_CLARO]
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig,use_container_width=True)


with col2:

    st.subheader("⏱ Garantías por Rango de Días")

    rango_df=(
    df_filtrado
    .groupby("rango_garantia")
    .size()
    .reset_index(name="cantidad")
    )

    fig=px.bar(
    rango_df,
    x="rango_garantia",
    y="cantidad",
    text="cantidad",
    color_discrete_sequence=[COLOR_AZUL_OSCURO]
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig,use_container_width=True)

# =====================================
# SEGUNDA FILA
# =====================================

col1,col2=st.columns(2)

with col1:

    st.subheader("🏢 Garantías por Contrata")

    contrata_df=(
    df_filtrado
    .groupby("contrata_causa_garantia")
    .size()
    .reset_index(name="cantidad")
    .sort_values("cantidad",ascending=False)
    )

    fig=px.bar(
    contrata_df,
    x="contrata_causa_garantia",
    y="cantidad",
    text="cantidad",
    color_discrete_sequence=[COLOR_AZUL_CLARO]
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig,use_container_width=True)

with col2:

    st.subheader("🛠 Top 15 Códigos de Cierre")

    codigos_df=(
    df_filtrado
    .groupby("codigo_completado")
    .size()
    .reset_index(name="cantidad")
    .sort_values("cantidad",ascending=False)
    .head(15)
    )

    fig=px.bar(
    codigos_df,
    x="cantidad",
    y="codigo_completado",
    orientation="h",
    text="cantidad",
    color_discrete_sequence=[COLOR_AZUL_OSCURO]
    )

    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig,use_container_width=True)

# =====================================
# TABLA TECNICOS
# =====================================

st.subheader("👨‍🔧 Garantías por Técnico")

tabla_tecnicos=(
df_filtrado
.groupby(["tecnico_causa_garantia","contrata_causa_garantia"])
.size()
.reset_index(name="garantias")
.sort_values("garantias",ascending=False)
)

st.dataframe(tabla_tecnicos,use_container_width=True)
