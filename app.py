import streamlit as st
import pandas as pd

st.title("Resumen de Órdenes por Técnico")

archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo)
    # Filtro por Contrata
    contratas = sorted(df["Contrata"].dropna().unique())
    contrata_seleccionada = st.selectbox("Filtrar por Contrata", ["Todas"] + list(contratas))

    if contrata_seleccionada != "Todas":
        df = df[df["Contrata"] == contrata_seleccionada]

    # Resumen por técnico
    resumen = df["Técnico"].value_counts().reset_index()
    resumen.columns = ["Técnico", "Órdenes"]

    st.subheader("Resultado:")
    st.dataframe(resumen)

    # Resumen por contrata
    st.subheader("Resumen por Contrata")
    resumen_contrata = df["Contrata"].value_counts().reset_index()
    resumen_contrata.columns = ["Contrata", "Órdenes"]
    st.dataframe(resumen_contrata)


