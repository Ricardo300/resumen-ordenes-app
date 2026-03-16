import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(layout="wide")

st.title("Carga de Materiales")

# conexión a supabase
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

archivo = st.file_uploader(
    "Subir archivo de materiales",
    type=["xlsx"]
)

if archivo is not None:

    df = pd.read_excel(archivo)

    # normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # verificar columnas
    columnas_necesarias = [
        "numero_orden",
        "material",
        "modelo",
        "serie",
        "cantidad"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            st.error(f"Falta la columna: {col}")
            st.stop()

    # limpiar datos
    df["serie"] = df["serie"].fillna("SIN_SERIE")
    df["serie"] = df["serie"].replace("", "SIN_SERIE")

    # asegurar tipos correctos
    df["numero_orden"] = df["numero_orden"].astype(str)
    df["material"] = df["material"].astype(str)
    df["modelo"] = df["modelo"].astype(str)
    df["serie"] = df["serie"].astype(str)
    df["cantidad"] = df["cantidad"].astype(float)

    st.subheader("Vista previa")
    st.dataframe(df.head(20))

    if st.button("Guardar materiales en base de datos"):

        datos = df.to_dict(orient="records")

        try:

            supabase.table("materiales_ordenes").upsert(
                datos,
                on_conflict="numero_orden,material,serie,modelo,cantidad"
            ).execute()

            st.success("Materiales cargados correctamente")

        except Exception as e:

            st.error(f"Error al guardar: {e}")
