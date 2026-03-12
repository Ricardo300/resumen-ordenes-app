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

    # ==========================================
    # CAPA 1 – DETECCIÓN DE MATERIALES
    # ==========================================

    preview = []
    facturacion = []

    for orden, grupo in ordenes:

        tipo_orden = grupo["TIPO DE ORDEN"].iloc[0]

        # ================================
        # DETECCIÓN DE MATERIALES
        # ================================

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

        SWITCH_VALIDOS = [
            "SWITCH DLINK DGS105"
        ]

        switch_count = grupo.loc[
            grupo["MATERIAL"].isin(SWITCH_VALIDOS),
            "CANTIDAD"
        ].sum()

        # ================================
        # DEFINIR TV SEGÚN TIPO DE ORDEN
        # ================================

        if "Traslado Externo" in tipo_orden:
            tv_count = grupo["TV"].fillna(0).iloc[0]
        else:
            tv_count = stb_count

        preview.append({
            "ORDEN": orden,
            "TIPO_ORDEN": tipo_orden,
            "FO_TOTAL": fo_total,
            "UTP_TOTAL": utp_total,
            "STB_COUNT": stb_count,
            "SWITCH_COUNT": switch_count
        })

        # ========================================
        # CAPA 2 – MOTOR DE REGLAS DE FACTURACIÓN
        # ========================================

        if "Traslado" in tipo_orden:
            concepto = "TRASLADO_SERVICIO"
        else:
            concepto = "MANO_OBRA_BASE"

        facturacion.append({
            "ORDEN": orden,
            "TIPO_ORDEN": tipo_orden,
            "CONCEPTO": concepto,
            "CANTIDAD": 1
        })

        # ================================
        # FO ADICIONAL
        # ================================

        if fo_total > 100:

            fo_adicional = fo_total - 100

            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS METRO ADICIONAL DE CABLE DROP DE FO",
                "CANTIDAD": fo_adicional
            })

        # ================================
        # UTP ADICIONAL
        # ================================

        utp_base = 5 * tv_count

        if utp_total > utp_base:

            utp_adicional = utp_total - utp_base

            # límite máximo de adicional
            utp_adicional = min(utp_adicional, 85)

            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS METRO ADICIONAL DE CABLE UTP GPON",
                "CANTIDAD": utp_adicional
            })

    # ========================================
    # RESULTADOS
    # ========================================

    preview_df = pd.DataFrame(preview)

    st.subheader("Cálculo de materiales por orden")
    st.dataframe(preview_df)

    facturacion_df = pd.DataFrame(facturacion)

    st.write("Total líneas generadas:", len(facturacion_df))
    st.subheader("Facturación generada por Python")
    st.dataframe(facturacion_df)
