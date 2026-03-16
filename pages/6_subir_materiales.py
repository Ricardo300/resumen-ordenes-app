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

    # leer archivo
    df = pd.read_excel(archivo)

    # normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # mapear posibles nombres de columnas de ETA
    df = df.rename(columns={
        "numero de orden": "numero_orden",
        "número de orden": "numero_orden",
        "orden": "numero_orden",
        "solicitud": "numero_orden",
        "serie equipo": "serie"
    })

    # verificar columnas necesarias
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
            st.write("Columnas detectadas:", df.columns)
            st.stop()

    # limpiar serie vacía
    df["serie"] = df["serie"].fillna("SIN_SERIE")
    df["serie"] = df["serie"].replace("", "SIN_SERIE")

    # eliminar NaN para que JSON sea válido
    df = df.fillna("")

    # asegurar tipos correctos
    df["numero_orden"] = df["numero_orden"].astype(str)
    df["material"] = df["material"].astype(str)
    df["modelo"] = df["modelo"].astype(str)
    df["serie"] = df["serie"].astype(str)
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0)

    st.subheader("Vista previa del archivo")
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
