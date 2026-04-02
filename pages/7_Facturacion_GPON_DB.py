import streamlit as st
import pandas as pd
import unicodedata
from supabase import create_client


def normalizar_texto(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


st.set_page_config(layout="wide")
st.title("Validación de Materiales GPON desde Supabase")
st.write("Consulta datos desde Supabase para validar la detección de materiales.")

# ==========================================
# CONEXIÓN SUPABASE
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

if st.button("Cargar datos"):

    # ==========================================
    # CONSULTAR VIEW BASE
    # ==========================================
    query = (
        supabase.table("view_base_facturacion")
        .select("*")
        .gte("fecha", str(fecha_inicio))
        .lte("fecha", str(fecha_fin))
        .execute()
    )

    data = query.data

    if len(data) == 0:
        st.warning("No hay datos en ese rango")
        st.stop()

    df = pd.DataFrame(data)

    # ==========================================
    # CARGAR TABLA DE PRECIOS
    # ==========================================
    query_precios = (
        supabase.table("precios_mano_obra")
        .select("*")
        .eq("activo", True)
        .execute()
    )

    df_precios = pd.DataFrame(query_precios.data)

    st.subheader("Tabla precios mano de obra")
    st.dataframe(df_precios, use_container_width=True)

    # ==========================================
    # CARGAR TABLA DE CONTRATISTAS
    # ==========================================
    query_contratistas = (
        supabase.table("contratistas_tarifa")
        .select("*")
        .eq("activo", True)
        .execute()
    )

    df_contratistas = pd.DataFrame(query_contratistas.data)

    st.subheader("Tabla contratistas")
    st.dataframe(df_contratistas, use_container_width=True)

    # ==========================================
    # ADAPTAR COLUMNAS EXACTAMENTE AL MOTOR ORIGINAL
    # ==========================================
    df.columns = df.columns.str.strip().str.upper()

    df = df.rename(columns={
        "ORDEN_TRABAJO": "NUMERO DE ORDEN",
        "SUB_TIPO_ORDEN": "TIPO DE ORDEN",
        "CANTIDAD_TV": "TV"
    })

    # ==========================================
    # VALIDAR COLUMNAS REQUERIDAS
    # ==========================================
    columnas_requeridas = [
        "NUMERO DE ORDEN",
        "TIPO DE ORDEN",
        "MATERIAL",
        "CANTIDAD",
        "TV"
    ]

    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if faltantes:
        st.error(f"Faltan columnas necesarias en el view: {faltantes}")
        st.stop()

    # ==========================================
    # CONVERTIR TIPOS NUMÉRICOS
    # ==========================================
    df["CANTIDAD"] = pd.to_numeric(df["CANTIDAD"], errors="coerce").fillna(0)
    df["TV"] = pd.to_numeric(df["TV"], errors="coerce").fillna(0)

    st.subheader("Vista previa del archivo")
    st.dataframe(df.head(20), use_container_width=True)

    st.subheader("Columnas detectadas")
    st.write(list(df.columns))

    # ==========================================
    # AGRUPAR POR ORDEN
    # ==========================================
    ordenes = df.groupby("NUMERO DE ORDEN")

    st.subheader("Órdenes detectadas")
    st.write("Total de órdenes:", len(ordenes))

    preview = []
    facturacion = []

    # ==========================================
    # CATÁLOGOS DE MATERIALES
    # ==========================================
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

    # ==========================================
    # RECORRER ÓRDENES
    # ==========================================
    for orden, grupo in ordenes:

        tipo_orden = str(grupo["TIPO DE ORDEN"].iloc[0])
        t = normalizar_texto(tipo_orden)

        # ==========================================
        # IDENTIFICAR REPARACIONES
        # ==========================================
        es_reparacion = (
            "REPARACION INTERNET (DGPON) + TV (GPON)" in t
            or "REPARACION INTERNET (GPON)" in t
            or "REPARACION LINEA FIJA (VGPON) + INTERNET (DGPON)" in t
            or "REPARACION LINEA FIJA (VGPON) + INTERNET (DGPON)+TV (GPON)" in t
        )

        # ================================
        # DETECCIÓN DE MATERIALES
        # ================================
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

        # ================================
        # DEFINIR TV SEGÚN TIPO DE ORDEN
        # ================================
        if "TRASLADO" in t:
            tv_count = pd.to_numeric(grupo["TV"], errors="coerce").fillna(0).iloc[0]
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

        # ========================================
        # MANO DE OBRA BASE POR TIPO DE SERVICIO
        # ========================================
        desc = ""
        cant = 1

        # ===============================
        # REPARACIONES
        # ===============================
        if es_reparacion:
            desc = "REVISION_ACTIVACION_CONF EQ GPON URBANO"

        # ===============================
        # CAMBIO DE PLAN
        # ===============================
        elif (
            "CAMBIO DE PLAN CON CAMBIO DE EQUIPO DATOS Y TV" in t
            or "CAMBIO DE PLAN CON CAMBIO DE EQUIPO TRIPLE PLAY" in t
        ):

            if stb_count == 1:
                sin_exist = 1
                con_exist = 0

            else:
                sin_exist = max(1, stb_count // 2)

                if stb_count % 2 == 1 and stb_count >= 3:
                    con_exist = 1
                else:
                    con_exist = 0

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

            cantidad_mo = stb_count if stb_count > 0 else 1

            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS ADICIONAL TV CON EXISTENTE VISITA 2",
                "CANTIDAD": cantidad_mo
            })

        elif "EQUIPO ADICIONAL TRIPLE PLAY" in t:

            cantidad_mo = stb_count if stb_count > 0 else 1

            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS ADICIONAL TV CON EXISTENTE VISITA 2",
                "CANTIDAD": cantidad_mo
            })

        elif "EQUIPO ADICIONAL DATOS" in t:

            equipos_datos = grupo["CANTIDAD"].sum()

            if equipos_datos > 0:
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

        elif "INSTALACION LINEA FIJA (VGPON) + INTERNET (DGPON)+TV (GPON)" in t:
            desc = "INSTALACIÓN TRIPLE PLAY TV, VOZ Y DATOS"

        elif "INSTALACION LINEA FIJA (VGPON) + INTERNET (DGPON)" in t:
            desc = "INSTALACIÓN TWO PLAY VOZ E INTERNET"

        # ===============================
        # TRASLADOS EXTERNOS
        # ===============================
        elif (
            "TRASLADO EXTERNO LINEA FIJA (VGPON) + INTERNET (DGPON)" in t
            and "+TV (GPON)" not in t
        ):
            desc = "TRASLADO SER EXTERNO 2PLAY VOZ/INTE GPON"

        elif "TRASLADO EXTERNO INTERNET (DGPON) + TV (GPON)" in t:
            desc = "TRASLADO SERVICIO EX 2PLAY INTER/TV GPON"

        elif "TRASLADO EXTERNO INTERNET (GPON)" in t:
            desc = "TRASLADO SERV EXTERNO 1PLAY INTERNE GPON"

        elif "TRASLADO EXTERNO LINEA FIJA (VGPON) + INTERNET (DGPON)+TV (GPON)" in t:
            desc = "TRASLADO DE SERVICIO EXTERNO 3PLAY GPON"

        # ===============================
        # TRASLADOS INTERNOS
        # ===============================
        elif "TRASLADO INTERNO INTERNET (GPON)" in t:
            desc = "TRASLADO SERVICIO INT ACOMETIDA COMPLETA"

        elif (
            "TRASLADO INTERNO DE INTERNET (GPON) + TV (GPON)" in t
            or "TRASLADO INTERNO INTERNET (GPON) + TV (GPON)" in t
            or "TRASLADO INTERNO LINEA FIJA (GPON) + INTERNET (GPON) + TV (GPON)" in t
            or "TRASLADO INTERNO LINEA FIJA (VGPON) + INTERNET (DGPON)+TV (GPON)" in t
            or "TRASLADO INTERNO LINEA FIJA (GPON) + INTERNET (GPON)+TV (GPON)" in t
        ):
            if tv_count >= 3:
                desc = "TRASLADO SERVICIO INT REUBICACION >=3STB"
            else:
                desc = "TRASLADO SERVICIO INT REUBICACION 2 STB"

        # ===============================
        # AGREGAR MANO DE OBRA BASE
        # ===============================
        if desc != "":
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": desc,
                "CANTIDAD": cant
            })

        # ================================
        # FO ADICIONAL
        # NO APLICA EN REPARACIONES
        # ================================
        if not es_reparacion and fo_total > 100:
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS METRO ADICIONAL DE CABLE DROP DE FO",
                "CANTIDAD": fo_total - 100
            })

        # ================================
        # UTP ADICIONAL
        # NO APLICA EN REPARACIONES
        # ================================
        utp_base = 5 * tv_count

        if not es_reparacion and utp_total > utp_base:
            utp_adicional = utp_total - utp_base
            utp_adicional = min(utp_adicional, 85)

            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS METRO ADICIONAL DE CABLE UTP GPON",
                "CANTIDAD": utp_adicional
            })

        # ================================
        # STB ADICIONAL (SOLO INSTALACIÓN)
        # NO APLICA EN REPARACIONES
        # ================================
        if not es_reparacion and "INSTALACION" in t and stb_count > 2:
            stb_adicional = stb_count - 2

            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INS ADICIONAL STB DE IPTV VISITA 1 GPON",
                "CANTIDAD": stb_adicional
            })

        # ================================
        # INSTALACION DE SWITCH
        # NO APLICA EN REPARACIONES
        # ================================
        if not es_reparacion and switch_count > 0:
            facturacion.append({
                "ORDEN": orden,
                "TIPO_ORDEN": tipo_orden,
                "CONCEPTO": "INSTALACION DE SWITCH ETHERNET PARA IPTV",
                "CANTIDAD": switch_count
            })

    # ==========================================
    # DATAFRAME RESUMEN DE MATERIALES
    # ==========================================
    preview_df = pd.DataFrame(preview)
    st.subheader("Cálculo de materiales por orden")
    st.dataframe(preview_df, use_container_width=True)

    # ==========================================
    # DATAFRAME DE FACTURACIÓN
    # ==========================================
    facturacion_df = pd.DataFrame(facturacion)

    # ==========================================
    # AGREGAR CONTRATA A FACTURACION
    # ==========================================
    df_contrata = df[["NUMERO DE ORDEN", "CONTRATA"]].drop_duplicates()

    facturacion_df = facturacion_df.merge(
        df_contrata,
        left_on="ORDEN",
        right_on="NUMERO DE ORDEN",
        how="left"
    )

    facturacion_df = facturacion_df.drop(columns=["NUMERO DE ORDEN"])

    # ==========================================
    # PREPARAR TABLA DE PRECIOS
    # ==========================================
    df_precios = df_precios.rename(columns={
        "descripcion_mo": "CONCEPTO"
    })

    # ==========================================
    # CRUCE CON PRECIOS
    # ==========================================
    facturacion_df = facturacion_df.merge(
        df_precios[[
            "CONCEPTO",
            "precio_venta",
            "precio_costo_estandar",
            "precio_costo_especial"
        ]],
        on="CONCEPTO",
        how="left"
    )

    # ==========================================
    # PREPARAR TABLA DE CONTRATISTAS
    # ==========================================
    df_contratistas = df_contratistas.rename(columns={
        "contratista": "CONTRATA"
    })

    # ==========================================
    # CRUCE CON TIPO DE TARIFA
    # ==========================================
    facturacion_df = facturacion_df.merge(
        df_contratistas[["CONTRATA", "tipo_tarifa_costo"]],
        on="CONTRATA",
        how="left"
    )

    # ==========================================
    # CALCULAR PRECIO COSTO
    # ==========================================
    facturacion_df["PRECIO_COSTO"] = facturacion_df.apply(
        lambda x: x["precio_costo_especial"]
        if x["tipo_tarifa_costo"] == "ESPECIAL"
        else x["precio_costo_estandar"],
        axis=1
    )

    # ==========================================
    # CALCULAR MONTOS
    # ==========================================
    facturacion_df["MONTO_VENTA"] = (
        facturacion_df["CANTIDAD"] * facturacion_df["precio_venta"]
    )

    facturacion_df["MONTO_COSTO"] = (
        facturacion_df["CANTIDAD"] * facturacion_df["PRECIO_COSTO"]
    )

    st.write("Total líneas generadas:", len(facturacion_df))
    st.subheader("Facturación generada por Python con precios")
    st.dataframe(facturacion_df, use_container_width=True)

    # ================================
    # REPORTE DE VALIDACIÓN DETALLADO
    # ================================
    mo_pivot = facturacion_df.pivot_table(
        index="ORDEN",
        columns="CONCEPTO",
        values="CANTIDAD",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    material_resumen = preview_df[[
        "ORDEN",
        "TIPO_ORDEN",
        "STB_COUNT",
        "UTP_TOTAL",
        "FO_TOTAL",
        "SWITCH_COUNT",
        "TV_COUNT"
    ]]

    reporte_validacion = material_resumen.merge(
        mo_pivot,
        on="ORDEN",
        how="left"
    ).fillna(0)

    st.subheader("Reporte de Validación Manual")
    st.dataframe(
        reporte_validacion,
        use_container_width=True
    )
