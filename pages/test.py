import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# =====================================
# CONFIGURACIÓN GENERAL
# =====================================

st.set_page_config(
    page_title="Dashboard Garantías",
    layout="wide"
)

st.title("Dashboard de Garantías")

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
            .select("orden_trabajo, fecha, contrata, tecnologia")
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

# =====================================
# CARGA DE DATOS
# =====================================

df = cargar_garantias()
df_servicios = cargar_servicios()

# =====================================
# VALIDACIÓN Y LIMPIEZA
# =====================================

if df.empty:
    st.warning("No se encontraron datos en vista_garantias.")
    st.stop()

if "fecha_garantia" in df.columns:
    df["fecha_garantia"] = pd.to_datetime(df["fecha_garantia"], errors="coerce")

if "contrata_causa_garantia" in df.columns:
    df["contrata_causa_garantia"] = df["contrata_causa_garantia"].fillna("SIN CONTRATA").astype(str).str.strip()

if "tipo_garantia" in df.columns:
    df["tipo_garantia"] = df["tipo_garantia"].fillna("SIN CLASIFICAR").astype(str).str.strip()

if "clasificacion_garantia" in df.columns:
    df["clasificacion_garantia"] = df["clasificacion_garantia"].fillna("SIN CLASIFICAR").astype(str).str.strip()

if "tecnico_causa_garantia" in df.columns:
    df["tecnico_causa_garantia"] = df["tecnico_causa_garantia"].fillna("SIN TECNICO").astype(str).str.strip()

if "codigo_completado" in df.columns:
    df["codigo_completado"] = df["codigo_completado"].fillna("SIN CODIGO").astype(str).str.strip()

if "rango_garantia" in df.columns:
    df["rango_garantia"] = df["rango_garantia"].fillna("SIN RANGO").astype(str).str.strip()

if "tecnologia" in df.columns:
    df["tecnologia"] = df["tecnologia"].fillna("SIN TECNOLOGIA").astype(str).str.strip()

if "dias_desde_visita" in df.columns:
    df["dias_desde_visita"] = pd.to_numeric(df["dias_desde_visita"], errors="coerce")

if not df_servicios.empty:
    if "fecha" in df_servicios.columns:
        df_servicios["fecha"] = pd.to_datetime(df_servicios["fecha"], errors="coerce")

    if "contrata" in df_servicios.columns:
        df_servicios["contrata"] = df_servicios["contrata"].fillna("SIN CONTRATA").astype(str).str.strip()

    if "tecnologia" in df_servicios.columns:
        df_servicios["tecnologia"] = df_servicios["tecnologia"].fillna("SIN TECNOLOGIA").astype(str).str.strip()

    if "orden_trabajo" in df_servicios.columns:
        df_servicios["orden_trabajo"] = df_servicios["orden_trabajo"].fillna("").astype(str).str.strip()
        df_servicios = df_servicios[df_servicios["orden_trabajo"] != ""]
        df_servicios = df_servicios[df_servicios["orden_trabajo"].str.upper() != "NONE"]

# =====================================
# COLUMNAS AUXILIARES
# =====================================

if "fecha_garantia" in df.columns:
    df["anio"] = df["fecha_garantia"].dt.year
    df["mes_num"] = df["fecha_garantia"].dt.month
else:
    df["anio"] = None
    df["mes_num"] = None

if not df_servicios.empty and "fecha" in df_servicios.columns:
    df_servicios["anio"] = df_servicios["fecha"].dt.year
    df_servicios["mes_num"] = df_servicios["fecha"].dt.month
else:
    df_servicios["anio"] = None
    df_servicios["mes_num"] = None

# =====================================
# HELPERS DE FILTRO
# =====================================

def filtro_checkbox(label, opciones, key_prefix, expanded=False):
    with st.sidebar.expander(label, expanded=expanded):
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

# =====================================
# FILTROS
# =====================================

st.sidebar.header("Filtros")

meses = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

hoy = datetime.today()
anio_actual = hoy.year
mes_actual = hoy.month

anios_disponibles = sorted([x for x in df["anio"].dropna().unique()])
meses_disponibles = sorted([x for x in df["mes_num"].dropna().unique()])

with st.sidebar.expander("Fecha", expanded=True):
    if anios_disponibles:
        index_anio = anios_disponibles.index(anio_actual) if anio_actual in anios_disponibles else len(anios_disponibles) - 1
        anio_sel = st.selectbox("Año", anios_disponibles, index=index_anio)
    else:
        anio_sel = None

    if meses_disponibles:
        index_mes = meses_disponibles.index(mes_actual) if mes_actual in meses_disponibles else len(meses_disponibles) - 1
        mes_sel = st.selectbox(
            "Mes",
            meses_disponibles,
            index=index_mes,
            format_func=lambda x: meses.get(x, str(x))
        )
    else:
        mes_sel = None

# Unión de contratas de garantías y servicios para que no falten opciones
opciones_contrata_garantias = sorted(df["contrata_causa_garantia"].dropna().unique()) if "contrata_causa_garantia" in df.columns else []
opciones_contrata_servicios = sorted(df_servicios["contrata"].dropna().unique()) if "contrata" in df_servicios.columns else []
opciones_contrata = sorted(list(set(opciones_contrata_garantias) | set(opciones_contrata_servicios)))

contrata_sel = filtro_checkbox("Contrata", opciones_contrata, "con", expanded=False)

opciones_tecnologia_garantias = sorted(df["tecnologia"].dropna().unique()) if "tecnologia" in df.columns else []
opciones_tecnologia_servicios = sorted(df_servicios["tecnologia"].dropna().unique()) if "tecnologia" in df_servicios.columns else []
opciones_tecnologia = sorted(list(set(opciones_tecnologia_garantias) | set(opciones_tecnologia_servicios)))

tecnologia_sel = filtro_checkbox("Tecnología", opciones_tecnologia, "tec", expanded=False)

# =====================================
# APLICAR FILTROS GARANTÍAS
# =====================================

df_filtrado = df.copy()

if anio_sel is not None:
    df_filtrado = df_filtrado[df_filtrado["anio"] == anio_sel]

if mes_sel is not None:
    df_filtrado = df_filtrado[df_filtrado["mes_num"] == mes_sel]

if contrata_sel:
    df_filtrado = df_filtrado[df_filtrado["contrata_causa_garantia"].isin(contrata_sel)]
else:
    df_filtrado = df_filtrado.iloc[0:0]

if tecnologia_sel:
    df_filtrado = df_filtrado[df_filtrado["tecnologia"].isin(tecnologia_sel)]
else:
    df_filtrado = df_filtrado.iloc[0:0]

df_filtrado = df_filtrado.reset_index(drop=True)

# =====================================
# APLICAR FILTROS SERVICIOS
# =====================================

servicios_filtrados = df_servicios.copy()

if anio_sel is not None:
    servicios_filtrados = servicios_filtrados[servicios_filtrados["anio"] == anio_sel]

if mes_sel is not None:
    servicios_filtrados = servicios_filtrados[servicios_filtrados["mes_num"] == mes_sel]

if contrata_sel:
    servicios_filtrados = servicios_filtrados[servicios_filtrados["contrata"].isin(contrata_sel)]
else:
    servicios_filtrados = servicios_filtrados.iloc[0:0]

if tecnologia_sel:
    servicios_filtrados = servicios_filtrados[servicios_filtrados["tecnologia"].isin(tecnologia_sel)]
else:
    servicios_filtrados = servicios_filtrados.iloc[0:0]

if "orden_trabajo" in servicios_filtrados.columns:
    total_servicios = servicios_filtrados["orden_trabajo"].nunique()
else:
    total_servicios = 0

# =====================================
# KPIs
# =====================================

ordenes_atendidas = total_servicios
total_garantias = len(df_filtrado)
garantias_internas = len(df_filtrado[df_filtrado["tipo_garantia"] == "INTERNA"])
garantias_externas = len(df_filtrado[df_filtrado["tipo_garantia"] == "EXTERNA"])
garantias_tecnico = len(df_filtrado[df_filtrado["clasificacion_garantia"] == "TECNICO"])

if total_servicios > 0:
    pct_garantia_interna = round((garantias_internas / total_servicios) * 100, 2)
    pct_garantia_tecnico = round((garantias_tecnico / total_servicios) * 100, 2)
else:
    pct_garantia_interna = 0
    pct_garantia_tecnico = 0

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("Órdenes Atendidas", f"{ordenes_atendidas:,}")
k2.metric("Total Garantías", f"{total_garantias:,}")
k3.metric("Garantías Internas", f"{garantias_internas:,}")
k4.metric("Garantías Externas", f"{garantias_externas:,}")
k5.metric("% Garantía Interna", f"{pct_garantia_interna}%")
k6.metric("% Garantía Técnico", f"{pct_garantia_tecnico}%")

# =====================================
# DEBUG
# =====================================

with st.expander("DEBUG SERVICIOS", expanded=True):
    base_serv = df_servicios.copy()

    st.write("Base total filas:", len(base_serv))
    st.write("Base órdenes únicas:", base_serv["orden_trabajo"].nunique() if "orden_trabajo" in base_serv.columns else 0)

    st.write("Servicios con fecha nula:", base_serv["fecha"].isna().sum() if "fecha" in base_serv.columns else 0)
    st.write("Servicios con orden_trabajo nulo/vacío:", (base_serv["orden_trabajo"].isna().sum() if "orden_trabajo" in base_serv.columns else 0))
    st.write("Servicios con contrata nula:", base_serv["contrata"].isna().sum() if "contrata" in base_serv.columns else 0)
    st.write("Servicios con tecnologia nula:", base_serv["tecnologia"].isna().sum() if "tecnologia" in base_serv.columns else 0)

    serv_ym = base_serv.copy()
    if anio_sel is not None:
        serv_ym = serv_ym[serv_ym["anio"] == anio_sel]
    if mes_sel is not None:
        serv_ym = serv_ym[serv_ym["mes_num"] == mes_sel]

    st.write("Solo año/mes - filas:", len(serv_ym))
    st.write("Solo año/mes - órdenes únicas:", serv_ym["orden_trabajo"].nunique() if "orden_trabajo" in serv_ym.columns else 0)

    serv_ymc = serv_ym.copy()
    if contrata_sel:
        serv_ymc = serv_ymc[serv_ymc["contrata"].isin(contrata_sel)]
    else:
        serv_ymc = serv_ymc.iloc[0:0]

    st.write("Año/mes + contrata - filas:", len(serv_ymc))
    st.write("Año/mes + contrata - órdenes únicas:", serv_ymc["orden_trabajo"].nunique() if "orden_trabajo" in serv_ymc.columns else 0)

    serv_ymct = serv_ymc.copy()
    if tecnologia_sel:
        serv_ymct = serv_ymct[serv_ymct["tecnologia"].isin(tecnologia_sel)]
    else:
        serv_ymct = serv_ymct.iloc[0:0]

    st.write("Año/mes + contrata + tecnología - filas:", len(serv_ymct))
    st.write("Año/mes + contrata + tecnología - órdenes únicas:", serv_ymct["orden_trabajo"].nunique() if "orden_trabajo" in serv_ymct.columns else 0)

# =====================================
# TABLA
# =====================================

st.write("Total servicios filtrados:", total_servicios)
st.write("Total garantías filtradas:", len(df_filtrado))

st.dataframe(df_filtrado, use_container_width=True)
