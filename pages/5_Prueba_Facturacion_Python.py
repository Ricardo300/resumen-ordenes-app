import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Prueba Motor de Facturación GPON")
st.write("Sube el mismo Excel que usas como base en el macro para comparar resultados.")

archivo = st.file_uploader("Subir archivo Excel base del macro", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo)

    st.subheader("Vista previa del archivo")
    st.dataframe(df.head(20))
  #detecta las columnas
    st.subheader("Columnas detectadas")
    st.write(list(df.columns))
