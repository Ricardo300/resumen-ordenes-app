import streamlit as st
import pandas as pd

st.title("Carga de Materiales")

archivo = st.file_uploader("Subir archivo de materiales", type=["xlsx"])

if archivo is not None:
    
    df = pd.read_excel(archivo)

    st.write("Columnas detectadas:")
    st.write(df.columns)

    st.write("Primeras filas del archivo:")
    st.dataframe(df.head())

# columnas que necesitamos
columnas_necesarias = [
    "NUMERO DE ORDEN",
    "MATERIAL",
    "CANTIDAD",
    "SERIE",
    "MODELO"
]

df_materiales = df[columnas_necesarias].copy()

st.write("Datos preparados para guardar:")
st.dataframe(df_materiales.head())
