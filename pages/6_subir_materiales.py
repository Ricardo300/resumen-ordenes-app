import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(layout="wide")
st.title("Carga de Materiales")

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

archivo = st.file_uploader("Subir archivo de materiales", type=["xlsx"])

if archivo is not None:

    df = pd.read_excel(archivo)

    df.columns = df.columns.str.strip().str.upper()

    st.subheader("Columnas detectadas")
    st.write(df.columns.tolist())

    st.subheader("Primeras filas del archivo")
    st.dataframe(df.head())

    columnas_necesarias = [
        "NUMERO DE ORDEN",
        "MATERIAL",
        "CANTIDAD",
        "SERIE",
        "MODELO"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = None

    df_materiales = df[columnas_necesarias].copy()

    df_materiales = df_materiales.dropna(subset=["NUMERO DE ORDEN"])

    st.subheader("Datos preparados para guardar")
    st.dataframe(df_materiales)

    df_db = df_materiales.rename(columns={
        "NUMERO DE ORDEN": "numero_orden",
        "MATERIAL": "material",
        "CANTIDAD": "cantidad",
        "SERIE": "serie",
        "MODELO": "modelo"
    })

    if st.button("Guardar materiales en base de datos"):

        try:

            df_db = df_db.astype(object)
            df_db = df_db.where(pd.notnull(df_db), None)

            datos = df_db.to_dict(orient="records")

            supabase.table("materiales_ordenes").upsert(
                datos,
                on_conflict="numero_orden,material,serie,modelo,cantidad"
            ).execute()

            st.success("Materiales guardados correctamente (sin duplicados)")

        except Exception as e:

            st.error(f"Error al guardar: {e}")
