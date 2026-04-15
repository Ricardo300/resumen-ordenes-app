import streamlit as st
import pandas as pd
from datetime import datetime

# =========================================================
# CONFIG PÁGINA
# =========================================================
st.set_page_config(page_title="Dashboard de Instalaciones", layout="wide")

# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
    }

    .titulo-dashboard {
        font-size: 34px;
        font-weight: 800;
        color: white;
        margin-bottom: 4px;
    }

    .subtitulo-dashboard {
        font-size: 14px;
        color: #cbd5e1;
        margin-bottom: 22px;
    }

    .bloque-tec {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 18px;
        padding: 18px 18px 14px 18px;
        margin-bottom: 14px;
    }

    .bloque-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }

    .bloque-titulo {
        font-size: 24px;
        font-weight: 800;
        color: white;
    }

    .bloque-total {
        font-size: 16px;
        font-weight: 700;
        color: #cbd5e1;
        background: #1f2937;
        padding: 6px 12px;
        border-radius: 10px;
    }

    .cards-row {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 10px;
    }

    .card-estado {
        border-radius: 16px;
        padding: 16px 10px;
        text-align: center;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.20);
    }

    .card-numero {
        font-size: 34px;
        font-weight: 900;
        color: white;
        line-height: 1.1;
        margin-bottom: 8px;
    }

    .card-estado-nombre {
        font-size: 15px;
        font-weight: 700;
        color: white;
        line-height: 1.2;
    }

    .no-clasificado-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 12px 16px;
        text-align: center;
        color: #e2e8f0;
        font-size: 16px;
        font-weight: 700;
        margin-top: 4px;
    }

    @media (max-width: 1200px) {
        .cards-row {
            grid-template-columns: repeat(3, 1fr);
        }
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNCIONES
# =========================================================
def buscar_columna(df, nombre_base):
    """
    Busca una columna aunque venga duplicada como Estado, Estado.1, etc.
    """
    cols = [c for c in df.columns if str(c).strip().lower().startswith(nombre_base.lower())]
    return cols[0] if cols else None


def normalizar_estado(valor):
    if pd.isna(valor):
        return "Sin Estado"

    txt = str(valor).strip()

    mapa_visual = {
        "pendiente": "Pendiente",
        "iniciado": "Iniciado",
        "suspendido": "Suspendido",
        "completado": "Completado",
        "cancelado": "Cancelado",
        "en ruta": "En ruta",
    }

    return mapa_visual.get(txt.lower(), txt.title())


def ordenar_estados(estados_encontrados):
    orden_base = ["Pendiente", "Iniciado", "En ruta", "Suspendido", "Completado", "Cancelado"]
    extras = [e for e in estados_encontrados if e not in orden_base]
    return orden_base + sorted(extras)


def color_estado(estado):
    colores = {
        "Pendiente":  "#f59e0b",  # naranja
        "Iniciado":   "#eab308",  # amarillo
        "En ruta":    "#3b82f6",  # azul
        "Suspendido": "#ef4444",  # rojo
        "Completado": "#22c55e",  # verde
        "Cancelado":  "#6b7280",  # gris
    }
    return colores.get(estado, "#64748b")


def render_bloque_tecnologia(nombre_bloque, df_tecnologia, estados_base):
    total = len(df_tecnologia)

    conteo = (
        df_tecnologia["estado_visual"]
        .value_counts(dropna=False)
        .to_dict()
    )

    cards_html = ""
    for estado in estados_base:
        valor = conteo.get(estado, 0)
        color = color_estado(estado)

        cards_html += f"""
        <div class="card-estado" style="background:{color};">
            <div class="card-numero">{valor}</div>
            <div class="card-estado-nombre">{estado}</div>
        </div>
        """

    st.markdown(f"""
    <div class="bloque-tec">
        <div class="bloque-header">
            <div class="bloque-titulo">{nombre_bloque}</div>
            <div class="bloque-total">Total {nombre_bloque}: {total}</div>
        </div>
        <div class="cards-row">
            {cards_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# EJEMPLO DE CARGA
# Si ya tienes df cargado antes, elimina este uploader
# y deja solo el bloque de procesamiento.
# =========================================================
archivo = st.file_uploader("Sube archivo ETA", type=["xlsx", "xls"])

if archivo is not None:
    df = pd.read_excel(archivo)

    # -----------------------------------------------------
    # DETECTAR COLUMNAS NECESARIAS
    # -----------------------------------------------------
    col_estado = buscar_columna(df, "Estado")
    col_tipo_actividad = buscar_columna(df, "Tipo Actividad")
    col_subtipo = buscar_columna(df, "Sub Tipo de Orden")

    if not col_estado or not col_tipo_actividad or not col_subtipo:
        st.error("No encontré una o más columnas necesarias: Estado, Tipo Actividad, Sub Tipo de Orden.")
        st.stop()

    # -----------------------------------------------------
    # LIMPIEZA: QUITAR ALMUERZOS
    # -----------------------------------------------------
    df = df.copy()

    df = df[
        ~df[col_tipo_actividad].astype(str).str.strip().isin([
            "Tiempo Almuerzo LU",
            "Tiempo de almuerzo"
        ])
    ].copy()

    # -----------------------------------------------------
    # CLASIFICAR TECNOLOGÍA
    # -----------------------------------------------------
    df["sub_tipo_orden"] = df[col_subtipo].astype(str).str.strip()

    map_tecnologia = {
        # DTH
        "Cambio de Plan con Cambio de Equipo DTH": "DTH",
        "Equipo Adicional TV": "DTH",
        "Instalación de Cajas Adicionales DTH": "DTH",
        "Instalación de servicio televisión DTH": "DTH",
        "Instalación de TV (DTH)": "DTH",
        "Cambio de Equipo TV": "DTH",
        "Reparacion DTH": "DTH",
        "Reparacion Linea Fija LFI": "DTH",
        "Reparación servicio DTH": "DTH",
        "Traslado Externo de TV (DTH)": "DTH",
        "Traslado Interno de Servicio de DTH": "DTH",
        "Traslado Interno de TV (DTH)": "DTH",
        "Traslado TV (DTH)": "DTH",

        # GPON
        "Cambio de Plan con Cambio de Equipo Datos y TV": "GPON",
        "Cambio de Plan con Cambio de Equipo Triple Play": "GPON",
        "Equipo Adicional Datos": "GPON",
        "Equipo Adicional Datos y TV": "GPON",
        "Equipo Adicional Triple Play": "GPON",
        "Equipo Adicional Vos y Datos": "GPON",
        "Instalacion Internet (DGPON)+TV (GPON)": "GPON",
        "Instalacion Internet (GPON)": "GPON",
        "Instalacion Línea fija (VGPON) + Internet (DGPON)": "GPON",
        "Instalacion Línea fija (VGPON) + Internet (DGPON)+TV (GPON)": "GPON",
        "Reparación Internet (DGPON) + TV (GPON)": "GPON",
        "Reparación Internet (GPON)": "GPON",
        "Reparación Línea fija (VGPON) + Internet (DGPON)": "GPON",
        "Reparación Línea fija (VGPON) + Internet (DGPON)+TV (GPON)": "GPON",
        "Traslado Externo Internet (DGPON) + TV (GPON)": "GPON",
        "Traslado Externo Internet (GPON)": "GPON",
        "Traslado Externo Línea fija (VGPON) + Internet (DGPON)": "GPON",
        "Traslado Externo Línea fija (VGPON) + Internet (DGPON)+TV (GPON)": "GPON",
        "Traslado Interno de Internet (GPON) + TV (GPON)": "GPON",
        "Traslado Interno Internet (GPON)": "GPON",
        "Traslado Interno Linea fIja (GPON) + Internet (GPON)": "GPON",
        "Traslado Interno Linea fIja (GPON) + Internet (GPON) + TV (GPON)": "GPON",
    }

    df["tecnologia"] = df["sub_tipo_orden"].map(map_tecnologia)
    df["tecnologia"] = df["tecnologia"].fillna("NO_CLASIFICADO")

    # -----------------------------------------------------
    # ESTADO VISUAL
    # -----------------------------------------------------
    df["estado_visual"] = df[col_estado].apply(normalizar_estado)

    # Estados encontrados + orden fijo
    estados_encontrados = list(df["estado_visual"].dropna().unique())
    estados_mostrar = ordenar_estados(estados_encontrados)

    # -----------------------------------------------------
    # ENCABEZADO
    # -----------------------------------------------------
    fecha_hora = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    total_registros = len(df)

    st.markdown('<div class="titulo-dashboard">Dashboard de Instalaciones</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="subtitulo-dashboard">Corte generado: {fecha_hora} &nbsp;&nbsp;|&nbsp;&nbsp; Registros operativos: {total_registros}</div>',
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # BLOQUES GPON Y DTH
    # -----------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        df_gpon = df[df["tecnologia"] == "GPON"].copy()
        render_bloque_tecnologia("GPON", df_gpon, estados_mostrar)

    with col2:
        df_dth = df[df["tecnologia"] == "DTH"].copy()
        render_bloque_tecnologia("DTH", df_dth, estados_mostrar)

    # -----------------------------------------------------
    # INDICADOR NO CLASIFICADO
    # -----------------------------------------------------
    no_clasificado = (df["tecnologia"] == "NO_CLASIFICADO").sum()

    st.markdown(
        f'<div class="no-clasificado-box">No clasificado: {no_clasificado}</div>',
        unsafe_allow_html=True
    )
