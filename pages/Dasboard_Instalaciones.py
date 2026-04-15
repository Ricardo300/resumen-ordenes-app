import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dashboard de Instalaciones", layout="wide")

# =========================================================
# ESTILO GENERAL
# =========================================================
st.markdown("""
<style>
.main {
    background-color: #0b1220;
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
    max-width: 98%;
}

.titulo-dashboard {
    font-size: 52px;
    font-weight: 900;
    color: white;
    line-height: 1.1;
    margin-bottom: 8px;
}

.subtitulo-dashboard {
    font-size: 22px;
    color: #cbd5e1;
    margin-bottom: 18px;
    font-weight: 600;
}

.no-clasificado {
    text-align: center;
    color: #e2e8f0;
    font-size: 24px;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 10px;
    background: #1e293b;
    border-radius: 16px;
    padding: 14px 20px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNCIONES
# =========================================================
def normalizar_estado(valor):
    if pd.isna(valor):
        return "Sin Estado"

    txt = str(valor).strip().lower()

    mapa = {
        "pendiente": "Pendiente",
        "iniciado": "Iniciado",
        "suspendido": "Suspendido",
        "completado": "Completado",
        "cancelado": "Cancelado",
        "en ruta": "En ruta",
    }

    return mapa.get(txt, txt.title())


def ordenar_estados(estados):
    orden_base = ["Pendiente", "Iniciado", "En ruta", "Suspendido", "Completado", "Cancelado"]
    extras = [e for e in estados if e not in orden_base]
    return orden_base + sorted(extras)


def color_estado(estado):
    colores = {
        "Pendiente": "#f59e0b",   # naranja
        "Iniciado": "#eab308",    # amarillo
        "En ruta": "#3b82f6",     # azul
        "Suspendido": "#ef4444",  # rojo
        "Completado": "#22c55e",  # verde
        "Cancelado": "#6b7280",   # gris
    }
    return colores.get(estado, "#64748b")


def render_bloque(nombre, df_bloque, estados):
    total = len(df_bloque)
    conteo = df_bloque["estado_visual"].value_counts().to_dict()

    cards_html = ""
    for estado in estados:
        valor = conteo.get(estado, 0)
        color = color_estado(estado)

        cards_html += f"""
        <div class="card-estado" style="background:{color};">
            <div class="card-numero">{valor}</div>
            <div class="card-estado-nombre">{estado}</div>
        </div>
        """

    html = f"""
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                background: transparent;
                font-family: Arial, sans-serif;
            }}

            .bloque-tec {{
                background: #0f1b33;
                border-radius: 24px;
                padding: 26px;
                min-height: 520px;
                box-sizing: border-box;
                border: 1px solid rgba(255,255,255,0.05);
            }}

            .bloque-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
            }}

            .bloque-titulo {{
                font-size: 42px;
                font-weight: 900;
                color: white;
                line-height: 1.1;
            }}

            .bloque-total {{
                font-size: 26px;
                color: #e2e8f0;
                background: #1e3358;
                padding: 14px 20px;
                border-radius: 18px;
                font-weight: 800;
            }}

            .cards-row {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 18px;
            }}

            .card-estado {{
                border-radius: 20px;
                padding: 20px 14px;
                min-height: 150px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                box-sizing: border-box;
                box-shadow: 0 6px 14px rgba(0,0,0,0.18);
            }}

            .card-numero {{
                font-size: 56px;
                font-weight: 900;
                color: white;
                line-height: 1;
                margin-bottom: 10px;
            }}

            .card-estado-nombre {{
                font-size: 22px;
                color: white;
                font-weight: 800;
                line-height: 1.15;
            }}
        </style>
    </head>
    <body>
        <div class="bloque-tec">
            <div class="bloque-header">
                <div class="bloque-titulo">{nombre}</div>
                <div class="bloque-total">Total {nombre}: {total}</div>
            </div>
            <div class="cards-row">
                {cards_html}
            </div>
        </div>
    </body>
    </html>
    """

    components.html(html, height=560, scrolling=False)


# =========================================================
# CARGA ARCHIVO
# =========================================================
archivo = st.file_uploader("Sube archivo ETA", type=["xlsx", "xls"])

if archivo is not None:
    df = pd.read_excel(archivo, engine="openpyxl")

    # =====================================================
    # VALIDACIÓN BÁSICA DE COLUMNAS
    # =====================================================
    columnas_necesarias = ["Estado", "Tipo Actividad", "Sub Tipo de Orden"]
    faltantes = [c for c in columnas_necesarias if c not in df.columns]

    if faltantes:
        st.error(f"Faltan estas columnas en el archivo: {', '.join(faltantes)}")
        st.stop()

    # =====================================================
    # LIMPIEZA: QUITAR ALMUERZOS
    # =====================================================
    df = df[~df["Tipo Actividad"].astype(str).str.strip().isin([
        "Tiempo Almuerzo LU",
        "Tiempo de almuerzo"
    ])].copy()

    # =====================================================
    # CLASIFICAR TECNOLOGÍA
    # =====================================================
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

    df["tecnologia"] = (
        df["Sub Tipo de Orden"]
        .astype(str)
        .str.strip()
        .map(map_tecnologia)
        .fillna("NO_CLASIFICADO")
    )

    # =====================================================
    # ESTADOS
    # =====================================================
    df["estado_visual"] = df["Estado"].apply(normalizar_estado)
    estados = ordenar_estados(list(df["estado_visual"].dropna().unique()))

    # =====================================================
    # ENCABEZADO
    # =====================================================
    st.markdown(
        '<div class="titulo-dashboard">Dashboard de Instalaciones</div>',
        unsafe_allow_html=True
    )

    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    st.markdown(
        f'<div class="subtitulo-dashboard">Corte: {fecha} | Registros operativos: {len(df)}</div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # BLOQUES PRINCIPALES
    # =====================================================
    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_bloque("GPON", df[df["tecnologia"] == "GPON"], estados)

    with col2:
        render_bloque("DTH", df[df["tecnologia"] == "DTH"], estados)

    # =====================================================
    # NO CLASIFICADO
    # =====================================================
    no_clasificado = (df["tecnologia"] == "NO_CLASIFICADO").sum()

    st.markdown(
        f'<div class="no-clasificado">No clasificado: {no_clasificado}</div>',
        unsafe_allow_html=True
    )
