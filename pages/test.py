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
# CARGA DE DATOS
# =====================================

response = supabase.table("vista_garantias").select("*").limit(1000).execute()
data = response.data
df = pd.DataFrame(data)

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

# =====================================
# COLUMNAS DE APOYO
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

anios = sorted([x for x in df["anio"].dropna().unique()])
meses = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

if anios:
    anio_sel = st.sidebar.selectbox("Año", anios, index=len(anios)-1)
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
tipo_sel = st.sidebar.multiselect("Tipo Garantía", tipos_disponibles, default=tipos_disponibles)

tecnologias_disponibles = sorted(df["tecnologia"].dropna().unique()) if "tecnologia" in df.columns else []
tec_sel = st.sidebar.multiselect("Tecnología", tecnologias_disponibles, default=tecnologias_disponibles)

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
# MOSTRAR RESULTADO
# =====================================

st.write("Total registros filtrados:", len(df_filtrado))
st.write("Columnas recibidas:")
st.write(df_filtrado.columns.tolist())

st.dataframe(df_filtrado, use_container_width=True)
