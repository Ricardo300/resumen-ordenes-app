import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Carga de Materiales")

archivo = st.file_uploader("Subir archivo de materiales", type=["xlsx"])

if archivo is not None:

    # ===============================
    # LEER EXCEL
    # ===============================
    df = pd.read_excel(archivo)

    # ===============================
    # LIMPIAR NOMBRES DE COLUMNAS
    # ===============================
    df.columns = df.columns.str.strip().str.upper()

    st.subheader("Columnas detectadas")
    st.write(df.columns.tolist())

    st.subheader("Primeras filas del archivo")
    st.dataframe(df.head())

    # ===============================
    # COLUMNAS QUE NECESITAMOS
    # ===============================
    columnas_necesarias = [
        "NUMERO DE ORDEN",
        "MATERIAL",
        "CANTIDAD",
        "SERIE",
        "MODELO"
    ]

    # ===============================
    # CREAR COLUMNAS SI NO EXISTEN
    # ===============================
    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = None

    # ===============================
    # FILTRAR COLUMNAS
    # ===============================
    df_materiales = df[columnas_necesarias].copy()

    # ===============================
    # LIMPIAR FILAS VACIAS
    # ===============================
    df_materiales = df_materiales.dropna(subset=["NUMERO DE ORDEN"])

    st.subheader("Datos preparados para guardar")
    st.dataframe(df_materiales)
