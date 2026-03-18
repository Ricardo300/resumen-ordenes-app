import streamlit as st
import pandas as pd
import unicodedata
from supabase import create_client

# ==========================================
# FUNCION NORMALIZAR TEXTO
# ==========================================
def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto

# ==========================================
# CONFIGURACION
# ==========================================
st.set_page_config(layout="wide")
st.title("Facturación GPON desde Supabase")

# ==========================================
# CONEXION SUPABASE
# ==========================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ==========================================
# FILTRO DE FECHAS
# ==========================================
fecha_inicio = st.date_input("Fecha inicio")
fecha_fin = st.date_input("Fecha fin")

# ==========================================
# BOTON CARGAR DATOS
# ==========================================
if st.button("Cargar datos"):

    query = supabase.table("view_base_facturacion") \
        .select("*") \
        .gte("fecha", str(fecha_inicio)) \
        .lte("fecha", str(fecha_fin)) \
        .execute()

    data = query.data

    if len(data) == 0:
        st.warning("No hay datos en ese rango")
        st.stop()

    df = pd.DataFrame(data)

    # ==========================================
    # ADAPTAR DATAFRAME AL MOTOR
    # ==========================================
    df_motor = df.copy()

    df_motor["NUMERO DE ORDEN"] = df_motor["orden_trabajo"]
    df_motor["MATERIAL"] = df_motor["material"]
    df_motor["CANTIDAD"] = df_motor["cantidad"]
    df_motor["TIPO DE ORDEN"] = df_motor["sub_tipo_orden"]
    df_motor["TV"] = df_motor["cantidad_tv"]

    df_motor["CANTIDAD"] = pd.to_numeric(df_motor["CANTIDAD"], errors="coerce").fillna(0)
    df_motor["TV"] = pd.to_numeric(df_motor["TV"], errors="coerce").fillna(0)

    st.subheader("Vista previa formato motor")
    st.dataframe(df_motor[["NUMERO DE ORDEN", "MATERIAL", "CANTIDAD", "TIPO DE ORDEN", "TV"]].head(20))

    # ==========================================
    # MOTOR DE CALCULO (TU CODIGO)
    # ==========================================

    ordenes = df_motor.groupby("NUMERO DE ORDEN")

    preview = []
    facturacion = []

    STB_VALIDAS = [
        "BUNDLE ZTE B866V2-H + CONTROL",
        "OTT PLAYER ZTE ZXV10 866V2",
        "OTT PLAYER ZTE ZXV10 866v2",
        "STB IPTV ZTE B866V2-H ANDROID",
        "STB IPTV ZTE ZXV10 866V2 SO ANDROID12",
        "STB IPTV ZTE ZXV10 866v2 SO ANDROID12",
        "STB IPTV ZTE ZXV10 866V2 SO ANDROID12(R)",
        "STB IPTV ZTE ZXV10 866v2 SO ANDROID12(R)",
        "STB SEI ROBOTICS ATV SEI800AMX"
    ]

    SWITCH_VALIDOS = [
        "SWITCH DLINK DGS105"
    ]

    for orden, grupo in ordenes:

        tipo_orden = str(grupo["TIPO DE ORDEN"].iloc[0])
        t = normalizar_texto(tipo_orden)

        fo_total = grupo.loc[
            grupo["MATERIAL"].astype(str).str.contains("CABLE OPTICO", case=False, na=False),
            "CANTIDAD"
        ].sum()

        utp_total = grupo.loc[
            grupo["MATERIAL"] == "CABLE UTP CAT5 P/INTERIORES 66445532AM",
            "CANTIDAD"
        ].sum()

        stb_count = grupo.loc[
            grupo["MATERIAL"].isin(STB_VALIDAS),
            "CANTIDAD"
        ].sum()

        switch_count = grupo.loc[
            grupo["MATERIAL"].isin(SWITCH_VALIDOS),
            "CANTIDAD"
        ].sum()

        if "TRASLADO" in t:
            tv_count = grupo["TV"].iloc[0]
        else:
            tv_count = stb_count

        preview.append({
            "ORDEN": orden,
            "TIPO_ORDEN": tipo_orden,
            "FO_TOTAL": fo_total,
            "UTP_TOTAL": utp_total,
            "STB_COUNT": stb_count,
            "SWITCH_COUNT": switch_count,
            "TV_COUNT": tv_count
        })

        desc = ""
        cant = 1

        if "INSTALACION INTERNET (DGPON)+TV (GPON)" in t:
            desc = "INSTALACIÓN TWO PLAY INTERNET Y TV"

        elif "INSTALACION INTERNET (GPON)" in t:
            desc = "INSTALACIÓN ONE PLAY DATOS"

        elif "TRASLADO EXTERNO INTERNET (DGPON) + TV (GPON)" in t:
            desc = "TRASLADO SERVICIO EX 2PLAY INTER/TV GPON"

        if desc != "":
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": desc,
                "CANTIDAD": cant
            })

        if fo_total > 100:
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS METRO ADICIONAL DE CABLE DROP DE FO",
                "CANTIDAD": fo_total - 100
            })

        utp_base = 5 * tv_count

        if utp_total > utp_base:
            utp_adicional = utp_total - utp_base
            utp_adicional = min(utp_adicional, 85)

            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS METRO ADICIONAL DE CABLE UTP GPON",
                "CANTIDAD": utp_adicional
            })

        if "INSTALACION" in t and stb_count > 2:
            stb_adicional = stb_count - 2

            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS ADICIONAL STB DE IPTV VISITA 1 GPON",
                "CANTIDAD": stb_adicional
            })

        if switch_count > 0:
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INSTALACION DE SWITCH ETHERNET PARA IPTV",
                "CANTIDAD": switch_count
            })

    preview_df = pd.DataFrame(preview)
    st.subheader("Cálculo de materiales por orden")
    st.dataframe(preview_df)

    facturacion_df = pd.DataFrame(facturacion)
    st.subheader("Facturación generada")
    st.dataframe(facturacion_df)

    # ==========================================
    # REPORTE VALIDACION
    # ==========================================
    if not facturacion_df.empty:

        mo_pivot = facturacion_df.pivot_table(
            index="ORDEN",
            columns="CONCEPTO",
            values="CANTIDAD",
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        material_resumen = preview_df

        reporte_validacion = material_resumen.merge(
            mo_pivot,
            on="ORDEN",
            how="left"
        ).fillna(0)

        st.subheader("Reporte de Validación")
        st.dataframe(reporte_validacion)
