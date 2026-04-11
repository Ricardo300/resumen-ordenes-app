import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# =====================================
# CONFIGURACIÓN GENERAL
# =====================================

st.set_page_config(
    page_title="Prueba Vista Garantías",
    layout="wide"
)

st.title("Prueba Vista Garantías")

# =====================================
# CONEXIÓN SUPABASE
# =====================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =====================================
# FUNCIÓN PARA CARGAR TODA LA VISTA
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

# =====================================
# CARGA DE DATOS
# =====================================

df = cargar_garantias()

# =====================================
# VALIDACIÓN Y LIMPIEZA
# =====================================

if df.empty:
    st.warning("No se encontraron datos en vista_garantias.")
    st.stop()

if "fecha_garantia" in df.columns:
    df["fecha_garantia"] = pd.to_datetime(df["fecha_garantia"], errors="coerce")

if "contrata_causa_garantia" in df.columns:
    df["contrata_causa_garantia"] = df["contrata_causa_garantia"].fillna("SIN CONTRATA")

if "tipo_garantia" in df.columns:
    df["tipo_garantia"] = df["tipo_garantia"].fillna("SIN CLASIFICAR")

if "clasificacion_garantia" in df.columns:
    df["clasificacion_garantia"] = df["clasificacion_garantia"].fillna("SIN CLASIFICAR")

if "tecnico_causa_garantia" in df.columns:
    df["tecnico_causa_garantia"] = df["tecnico_causa_garantia"].fillna("SIN TECNICO")

if "codigo_completado" in df.columns:
    df["codigo_completado"] = df["codigo_completado"].fillna("SIN CODIGO")

if "rango_garantia" in df.columns:
    df["rango_garantia"] = df["rango_garantia"].fillna("SIN RANGO")

if "tecnologia" in df.columns:
    df["tecnologia"] = df["tecnologia"].fillna("SIN TECNOLOGIA")

if "tipo_actividad" in df.columns:
    df["tipo_actividad"] = df["tipo_actividad"].fillna("SIN TIPO ACTIVIDAD")

if "dias_desde_visita" in df.columns:
    df["dias_desde_visita"] = pd.to_numeric(df["dias_desde_visita"], errors="coerce")

# =====================================
# COLUMNAS AUXILIARES
# =====================================

if "fecha_garantia" in df.columns:
    df["anio"] = df["fecha_garantia"].dt.year
    df["mes_num"] = df["fecha_garantia"].dt.month
else:
    df["anio"] = None
    df["mes_num"] = None

# =====================================
# HELPERS DE FILTRO
# =====================================

def filtro_checkbox(label, opciones, key_prefix, seleccion_default=None, expanded=False):
    if seleccion_default is None:
        seleccion_default = opciones.copy()

    # inicializar session state
    for opcion in opciones:
        estado_key = f"{key_prefix}_{opcion}"
        if estado_key not in st.session_state:
            st.session_state[estado_key] = opcion in seleccion_default

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
            estado = st.checkbox(opcion, key=f"{key_prefix}_{opcion}")
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

# ----- FECHA -----
anios_disponibles = sorted([x for x in df["anio"].dropna().unique()])
meses_disponibles = sorted([x for x in df["mes_num"].dropna().unique()])

with st.sidebar.expander("Fecha", expanded=True):
    if anios_disponibles:
        if anio_actual in anios_disponibles:
            index_anio = anios_disponibles.index(anio_actual)
        else:
            index_anio = len(anios_disponibles) - 1

        anio_sel = st.selectbox("Año", anios_disponibles, index=index_anio)
    else:
        anio_sel = None

    if meses_disponibles:
        if mes_actual in meses_disponibles:
            index_mes = meses_disponibles.index(mes_actual)
        else:
            index_mes = len(meses_disponibles) - 1

        mes_sel = st.selectbox(
            "Mes",
            meses_disponibles,
            index=index_mes,
            format_func=lambda x: meses.get(x, str(x))
        )
    else:
        mes_sel = None

# ----- CONTRATA -----
opciones_contrata = sorted(df["contrata_causa_garantia"].dropna().unique()) if "contrata_causa_garantia" in df.columns else []
contrata_sel = filtro_checkbox(
    "Contrata",
    opciones_contrata,
    "con",
    seleccion_default=opciones_contrata,
    expanded=False
)

# ----- TECNOLOGÍA -----
opciones_tecnologia = sorted(df["tecnologia"].dropna().unique()) if "tecnologia" in df.columns else []
tecnologia_sel = filtro_checkbox(
    "Tecnología",
    opciones_tecnologia,
    "tec",
    seleccion_default=opciones_tecnologia,
    expanded=False
)

# ----- TIPO ACTIVIDAD -----
opciones_tipo_actividad = sorted(df["tipo_actividad"].dropna().unique()) if "tipo_actividad" in df.columns else []
tipo_actividad_sel = filtro_checkbox(
    "Tipo Actividad",
    opciones_tipo_actividad,
    "act",
    seleccion_default=opciones_tipo_actividad,
    expanded=False
)

# =====================================
# APLICAR FILTROS
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

if tipo_actividad_sel:
    df_filtrado = df_filtrado[df_filtrado["tipo_actividad"].isin(tipo_actividad_sel)]
else:
    df_filtrado = df_filtrado.iloc[0:0]

df_filtrado = df_filtrado.reset_index(drop=True)

# =====================================
# MOSTRAR RESULTADOS
# =====================================

st.write("Total registros filtrados:", len(df_filtrado))

st.dataframe(df_filtrado, use_container_width=True)
