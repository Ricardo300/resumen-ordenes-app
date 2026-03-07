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
# CARGAR GARANTÍAS
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

    df = pd.DataFrame(todos)

    return df


# =====================================
# CARGAR SERVICIOS
# =====================================

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

    df = pd.DataFrame(todos)

    df["fecha"] = pd.to_datetime(df["fecha"])

    df["anio"] = df["fecha"].dt.year
    df["mes_num"] = df["fecha"].dt.month

    return df


df = cargar_garantias()
df_servicios = cargar_servicios()

# =====================================
# LIMPIEZA DATOS
# =====================================

df["fecha_garantia"] = pd.to_datetime(df["fecha_garantia"])

df["contrata_causa_garantia"] = df["contrata_causa_garantia"].fillna("SIN CONTRATA")
df["tipo_garantia"] = df["tipo_garantia"].fillna("SIN CLASIFICAR")
df["clasificacion_garantia"] = df["clasificacion_garantia"].fillna("SIN CLASIFICAR")

if "tecnologia" not in df.columns:
    df["tecnologia"] = "DESCONOCIDA"
else:
    df["tecnologia"] = df["tecnologia"].fillna("SIN TECNOLOGIA")

df["anio"] = df["fecha_garantia"].dt.year
df["mes_num"] = df["fecha_garantia"].dt.month

# =====================================
# FILTROS
# =====================================

st.sidebar.header("Filtros")

# Año

anios = sorted(df["anio"].unique())

anio_filtro = st.sidebar.selectbox(
    "Año",
    anios,
    index=len(anios)-1
)

# Mes

meses = {
1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
}

mes_num = st.sidebar.selectbox(
    "Mes",
    list(meses.keys()),
    format_func=lambda x: meses[x]
)

# =====================================
# FILTRO CHECKBOX
# =====================================

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

            if f"{key_prefix}_{opcion}" not in st.session_state:
                st.session_state[f"{key_prefix}_{opcion}"] = True

            estado = st.checkbox(opcion, key=f"{key_prefix}_{opcion}")

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
]

servicios_mes = df_servicios[
    (df_servicios["anio"] == anio_filtro) &
    (df_servicios["mes_num"] == mes_num)
]

total_servicios = len(servicios_mes)

# =====================================
# KPIs
# =====================================

total_garantias = len(df_filtrado)

garantias_internas = len(
    df_filtrado[df_filtrado["tipo_garantia"] == "INTERNA"]
)

garantias_externas = len(
    df_filtrado[df_filtrado["tipo_garantia"] == "EXTERNA"]
)

garantias_tecnico = len(
    df_filtrado[df_filtrado["clasificacion_garantia"] == "TECNICO"]
)

promedio_dias = round(df_filtrado["dias_desde_visita"].mean(),1)

if total_servicios > 0:

    pct_garantia_interna = round((garantias_internas / total_servicios)*100,2)
    pct_garantia_tecnico = round((garantias_tecnico / total_servicios)*100,2)

else:

    pct_garantia_interna = 0
    pct_garantia_tecnico = 0


col1,col2,col3,col4,col5,col6 = st.columns(6)

col1.metric("Total Garantías", total_garantias)
col2.metric("Garantías Internas", garantias_internas)
col3.metric("Garantías Externas", garantias_externas)
col4.metric("Promedio días", promedio_dias)
col5.metric("% Garantía Interna", f"{pct_garantia_interna}%")
col6.metric("% Garantía Técnico", f"{pct_garantia_tecnico}%")

# =====================================
# GARANTÍAS POR CONTRATA
# =====================================

st.subheader("Garantías por Contrata")

garantias_contrata = (
    df_filtrado
    .groupby("contrata_causa_garantia")
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

st.plotly_chart(fig, use_container_width=True)

# =====================================
# TABLA GARANTÍAS POR TÉCNICO
# =====================================

st.subheader("Garantías por Técnico")

garantias_tecnico = (
    df_filtrado
    .groupby(["tecnico_causa_garantia","contrata_causa_garantia"])
    .size()
    .reset_index(name="garantias")
    .sort_values("garantias", ascending=False)
)

garantias_tecnico = garantias_tecnico.rename(columns={
    "tecnico_causa_garantia":"Tecnico",
    "contrata_causa_garantia":"Contrata"
})

st.dataframe(
    garantias_tecnico,
    use_container_width=True,
    hide_index=True
)
# =====================================
# GARANTÍAS POR RANGO
# =====================================

st.subheader("Garantías por Rango de Días")

garantias_rango = (
    df_filtrado
    .groupby("rango_garantia")
    .size()
    .reset_index(name="cantidad")
)

orden = ["0-7","8-15","16-30","31-60","61-90",">90"]

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

st.plotly_chart(fig_rango, use_container_width=True)

# =====================================
# TOP 15 CODIGOS DE CIERRE
# =====================================

st.subheader("Top 15 Códigos de Cierre")

codigos_cierre = (
    df_filtrado
    .groupby("codigo_completado")
    .size()
    .reset_index(name="cantidad")
    .sort_values("cantidad", ascending=False)
    .head(15)
)

codigos_cierre = codigos_cierre.rename(columns={
    "codigo_completado":"Código de Cierre",
    "cantidad":"Garantías"
})

st.dataframe(
    codigos_cierre,
    use_container_width=True,
    hide_index=True
)


