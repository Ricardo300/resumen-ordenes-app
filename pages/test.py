import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(layout="wide")

st.title("Prueba Vista Garantías")

# conexión
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# consulta simple
response = supabase.table("vista_garantias").select("*").limit(100).execute()

data = response.data

# convertir a DataFrame
df = pd.DataFrame(data)

#LIMPIEZA BASICA
if df.empty:
    st.warning("No se encontraron datos en vista_garantias.")
    st.stop()

st.write("Columnas recibidas:")
st.write(df.columns.tolist())

# limpieza básica segura
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

st.dataframe(df)
# mostrar
st.write("Columnas:", df.columns.tolist())
st.dataframe(df)
