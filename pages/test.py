import streamlit as st
from supabase import create_client
import pandas as pd

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
# VALIDACIÓN Y LIMPIEZA BÁSICA
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
# FILTROS
# =====================================

st.sidebar.header("Filtros")

meses = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

anios = sorted([x for x in df["anio"].dropna().unique()])
if anios:
    anio_sel = st.sidebar.selectbox("Año", anios, index=len(anios) - 1)
else:
    anio_sel = None

meses_disponibles = sorted([x for x in df["mes_num"].dropna().unique()])
if meses_disponibles:
    mes_sel = st.sidebar.selectbox(
        "Mes",
        meses_disponibles,
        format_func=lambda x: meses.get(x, str(x))
    )
else:
    mes_sel = None

tipos_disponibles = sorted(df["tipo_garantia"].dropna().unique()) if "tipo_garantia" in df.columns else []
tipo_sel = st.sidebar.multiselect(
    "Tipo Garantía",
    tipos_disponibles,
    default=tipos_disponibles
)

tecnologias_disponibles = sorted(df["tecnologia"].dropna().unique()) if "tecnologia" in df.columns else []
tec_sel = st.sidebar.multiselect(
    "Tecnología",
    tecnologias_disponibles,
    default=tecnologias_disponibles
)

# =====================================
# APLICAR FILTROS
# =====================================

df_filtrado = df.copy()

if anio_sel is not None:
    df_filtrado = df_filtrado[df_filtrado["anio"] == anio_sel]

if mes_sel is not None:
    df_filtrado = df_filtrado[df_filtrado["mes_num"] == mes_sel]

if tipo_sel:
    df_filtrado = df_filtrado[df_filtrado["tipo_garantia"].isin(tipo_sel)]

if tec_sel:
    df_filtrado = df_filtrado[df_filtrado["tecnologia"].isin(tec_sel)]

# =====================================
# MOSTRAR RESULTADOS
# =====================================

st.write("Total registros cargados desde la vista:", len(df))
st.write("Total registros luego de filtros:", len(df_filtrado))

st.write("Valores seleccionados:")
st.write({
    "anio": anio_sel,
    "mes": meses.get(mes_sel, mes_sel) if mes_sel is not None else None,
    "tipos_garantia": tipo_sel,
    "tecnologias": tec_sel
})

st.dataframe(df_filtrado, use_container_width=True)
