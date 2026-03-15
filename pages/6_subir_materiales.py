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
