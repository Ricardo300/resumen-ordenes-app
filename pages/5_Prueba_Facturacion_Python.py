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

    st.subheader("Columnas detectadas")
    st.write(list(df.columns))

    # agrupar órdenes
    ordenes = df.groupby("NUMERO DE ORDEN")

    st.subheader("Órdenes detectadas")
    st.write("Total de órdenes:", len(ordenes))

    st.subheader("Cálculo de materiales por orden")

    preview = []
    facturacion = []

    for orden, grupo in ordenes:

        tipo_orden = grupo["TIPO DE ORDEN"].iloc[0]
        
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
            "ORDEN": orden,
            "FO_TOTAL": fo_total,
            "UTP_TOTAL": utp_total,
            "STB_COUNT": stb_count,
            "SWITCH_COUNT": switch_count
        })

        facturacion.append({
            "ORDEN": orden,
            "CONCEPTO": "MANO_OBRA_BASE",
            "CANTIDAD": 1
        })

    preview_df = pd.DataFrame(preview)

    st.dataframe(preview_df.head(20))

    facturacion_df = pd.DataFrame(facturacion)

    st.subheader("Facturación generada por Python")
    st.dataframe(facturacion_df)
