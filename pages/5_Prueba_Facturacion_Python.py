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

        if "Traslado" in tipo_orden:
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
        # ========================================
        # MANO DE OBRA BASE POR TIPO DE SERVICIO
        # ========================================
        
        t = tipo_orden.upper()
        
        desc = ""
        cant = 1
        
        # ===============================
        # CAMBIO DE PLAN
        # ===============================
        
        if "CAMBIO DE PLAN CON CAMBIO DE EQUIPO DATOS Y TV" in t \
        or "CAMBIO DE PLAN CON CAMBIO DE EQUIPO TRIPLE PLAY" in t:
        
            if stb_count <= 1:
                sin_exist = 1
                con_exist = 0
            else:
                sin_exist = max(1, stb_count // 2)
                con_exist = 1 if (stb_count >= 3 and stb_count % 2 == 1) else 0
        
            if sin_exist > 0:
                facturacion.append({
                    "ORDEN": orden,
                    "TIPO_ORDEN": tipo_orden,
                    "CONCEPTO": "INS ADICIONAL TV SIN EXISTENTE VISITA 2",
                    "CANTIDAD": sin_exist
                })
        
            if con_exist > 0:
                facturacion.append({
                    "ORDEN": orden,
                    "TIPO_ORDEN": tipo_orden,
                    "CONCEPTO": "INS ADICIONAL TV CON EXISTENTE VISITA 2",
                    "CANTIDAD": con_exist
                })
        
        
        # ===============================
        # EQUIPO ADICIONAL
        # ===============================
        
        elif "EQUIPO ADICIONAL DATOS Y TV" in t:
        
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS ADICIONAL TV CON EXISTENTE VISITA 2",
                "CANTIDAD": 1
            })
        
        elif "EQUIPO ADICIONAL TRIPLE PLAY" in t:
        
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS ADICIONAL TV CON EXISTENTE VISITA 2",
                "CANTIDAD": 1
            })
        
        elif "EQUIPO ADICIONAL DATOS" in t:
        
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "CONEXION/CONFIGURACION EXTENSORES WIFI",
                "CANTIDAD": 1
            })
        
        
        # ===============================
        # INSTALACIONES
        # ===============================
        
        elif "INSTALACION INTERNET (DGPON)+TV (GPON)" in t:
        
            desc = "INSTALACIÓN TWO PLAY INTERNET Y TV"
        
        elif "INSTALACION INTERNET (GPON)" in t:
        
            desc = "INSTALACIÓN ONE PLAY DATOS"
        
        elif "INSTALACION LÍNEA FIJA (VGPON) + INTERNET (DGPON)+TV (GPON)" in t \
        or "INSTALACION LINEA FIJA (VGPON) + INTERNET (DGPON)+TV (GPON)" in t:
        
            desc = "INSTALACIÓN TRIPLE PLAY TV, VOZ Y DATOS"
        
        elif "INSTALACION LÍNEA FIJA (VGPON) + INTERNET (DGPON)" in t \
        or "INSTALACION LINEA FIJA (VGPON) + INTERNET (DGPON)" in t:
        
            desc = "INSTALACIÓN TWO PLAY VOZ E INTERNET"
        
        
        # ===============================
        # TRASLADOS EXTERNOS
        # ===============================
        
        elif "TRASLADO EXTERNO LÍNEA FIJA (VGPON) + INTERNET (DGPON)" in t \
        or "TRASLADO EXTERNO LINEA FIJA (VGPON) + INTERNET (DGPON)" in t:
        
            desc = "TRASLADO SER EXTERNO 2PLAY VOZ/INTE GPON"
        
        elif "TRASLADO EXTERNO INTERNET (DGPON) + TV (GPON)" in t:
        
            desc = "TRASLADO SERVICIO EX 2PLAY INTER/TV GPON"
        
        elif "TRASLADO EXTERNO INTERNET (GPON)" in t:
        
            desc = "TRASLADO SERV EXTERNO 1PLAY INTERNE GPON"
        
        elif "TRASLADO EXTERNO LÍNEA FIJA (VGPON) + INTERNET (DGPON)+TV (GPON)" in t \
        or "TRASLADO EXTERNO LINEA FIJA (VGPON) + INTERNET (DGPON)+TV (GPON)" in t:
        
            desc = "TRASLADO DE SERVICIO EXTERNO 3PLAY GPON"
        
        
        # ===============================
        # TRASLADOS INTERNOS
        # ===============================
        
        elif "TRASLADO INTERNO INTERNET (GPON)" in t:
        
            desc = "TRASLADO SERVICIO INT ACOMETIDA COMPLETA"
        
        elif "TRASLADO INTERNO DE INTERNET (GPON) + TV (GPON)" in t:
        
            if tv_count >= 3:
                desc = "TRASLADO SERVICIO INT REUBICACION >=3STB"
            else:
                desc = "TRASLADO SERVICIO INT REUBICACION 2 STB"
        
        elif "TRASLADO INTERNO LINEA FIJA (GPON) + INTERNET (GPON) + TV (GPON)" in t:
        
            if tv_count >= 3:
                desc = "TRASLADO SERVICIO INT REUBICACION >=3STB"
            else:
                desc = "TRASLADO SERVICIO INT REUBICACION 2 STB"
        
        
        # ===============================
        # GENERAR LINEA
        # ===============================
        
        if desc != "":
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": desc,
                "CANTIDAD": cant
            })
       

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
        # ================================
        # STB ADICIONAL (SOLO INSTALACIÓN)
        # ================================
        
        if "Instal" in tipo_orden and stb_count > 2:
        
            stb_adicional = stb_count - 2
        
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS ADICIONAL STB DE IPTV VISITA 1 GPON",
                "CANTIDAD": stb_adicional
            })

        # ================================
        # INSTALACION DE SWITCH
        # ================================
        
        if switch_count > 0:
        
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INSTALACION DE SWITCH ETHERNET PARA IPTV",
                "CANTIDAD": switch_count
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
