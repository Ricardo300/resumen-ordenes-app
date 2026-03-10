import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Prueba Motor de Facturación GPON")
st.write("Sube el mismo Excel que usas como base en el macro para comparar resultados.")

archivo = st.file_uploader("Subir archivo Excel base del macro", type=["xlsx"])

if archivo is not None:

    df = pd.read_excel(archivo)

    # limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.upper()

    st.subheader("Vista previa del archivo")
    st.dataframe(df.head(20))

    # mostrar columnas
    st.subheader("Columnas detectadas")
    st.write(list(df.columns))

    # detectar órdenes
    st.subheader("Órdenes detectadas")

    ordenes = df.groupby("NUMERO DE ORDEN")

    st.subheader("Cálculo de materiales por orden")

preview = []

for orden, grupo in ordenes:

    fo_total = grupo.loc[
        grupo["MATERIAL"].str.contains("CABLE OPTICO", case=False, na=False),
        "CANTIDAD"
    ].sum()

    utp_total = grupo.loc[
        grupo["MATERIAL"].str.contains("UTP", case=False, na=False),
        "CANTIDAD"
    ].sum()

    stb_count = grupo.loc[
        grupo["MATERIAL"].str.contains("STB|ZXV10|B866", case=False, na=False),
        "CANTIDAD"
    ].sum()

    switch_count = grupo.loc[
        grupo["MATERIAL"].str.contains("SWITCH", case=False, na=False),
        "CANTIDAD"
    ].sum()

    preview.append({
        "orden": orden,
        "FO_total": fo_total,
        "UTP_total": utp_total,
        "STB_count": stb_count,
        "SWITCH_count": switch_count
    })

preview_df = pd.DataFrame(preview)

st.dataframe(preview_df.head(20))

    st.write("Total de órdenes:", len(ordenes))
