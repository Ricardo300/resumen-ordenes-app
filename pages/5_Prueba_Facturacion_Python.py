import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Validación de Materiales GPON")
st.write("Sube el Excel base para validar la detección de materiales.")

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

    preview = []

    for orden, grupo in ordenes:

        tipo_orden = grupo["TIPO DE ORDEN"].iloc[0]

        fo_total = grupo.loc[
            grupo["MATERIAL"].str.contains("CABLE OPTICO", case=False, na=False),
            "CANTIDAD"
        ].sum()

        utp_total = grupo.loc[
            grupo["MATERIAL"] == "CABLE UTP CAT5 P/INTERIORES 66445532AM",
            "CANTIDAD"
        ].sum()

        STB_VALIDAS = [
            "BUNDLE ZTE B866V2-H + CONTROL",
            "OTT PLAYER ZTE ZXV10 866v2",
            "STB IPTV ZTE B866V2-H ANDROID",
            "STB IPTV ZTE ZXV10 866v2 SO ANDROID12",
            "STB IPTV ZTE ZXV10 866v2 SO ANDROID12(R)",
            "STB SEI ROBOTICS ATV SEI800AMX"
        ]
        
        stb_count = grupo.loc[
            grupo["MATERIAL"].isin(STB_VALIDAS),
            "CANTIDAD"
        ].sum()

        switch_count = grupo.loc[
            grupo["MATERIAL"].str.contains("SWITCH", case=False, na=False),
            "CANTIDAD"
        ].sum()

        preview.append({
            "ORDEN": orden,
            "TIPO_ORDEN": tipo_orden,
            "FO_TOTAL": fo_total,
            "UTP_TOTAL": utp_total,
            "STB_COUNT": stb_count,
            "SWITCH_COUNT": switch_count
        })

    preview_df = pd.DataFrame(preview)

    st.subheader("Detección de materiales por orden")
    st.dataframe(preview_df)
