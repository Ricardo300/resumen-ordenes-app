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
:root {
    --bg-main: #060b16;
    --panel-bg: #0d1b34;
    --panel-border: rgba(255,255,255,0.08);
    --text-main: #ffffff;
    --text-soft: #cbd5e1;
    --badge-bg: #1c3663;
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #050913 0%, #08101d 100%);
}

.main {
    background: transparent;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 98%;
}

header, footer {
    visibility: hidden;
}

.titulo-dashboard {
    font-size: 56px;
    font-weight: 900;
    color: var(--text-main);
    line-height: 1.05;
    margin-bottom: 8px;
    letter-spacing: 0.3px;
}

.subtitulo-dashboard {
    font-size: 22px;
    color: var(--text-soft);
    margin-bottom: 20px;
    font-weight: 600;
}

.no-clasificado {
    text-align: center;
    color: #e5edf8;
    font-size: 24px;
    font-weight: 800;
    margin-top: 12px;
    margin-bottom: 8px;
    background: linear-gradient(180deg, #1a2b49 0%, #14233d 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px 22px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.18);
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
        "Pendiente": "#f4a300",
        "Iniciado": "#d9ad00",
        "En ruta": "#3f83f8",
        "Suspendido": "#ef4444",
        "Completado": "#22c55e",
        "Cancelado": "#7b8496",
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
                background: linear-gradient(180deg, #0b1a34 0%, #0a1730 100%);
                border-radius: 26px;
                padding: 28px;
                min-height: 540px;
                box-sizing: border-box;
                border: 1px solid rgba(255,255,255,0.07);
                box-shadow:
                    0 14px 28px rgba(0,0,0,0.22),
                    inset 0 1px 0 rgba(255,255,255,0.03);
            }}

            .bloque-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
            }}

            .bloque-titulo {{
                font-size: 44px;
                font-weight: 900;
                color: white;
                line-height: 1.05;
                letter-spacing: 0.4px;
            }}

            .bloque-total {{
                font-size: 28px;
                color: #f1f5f9;
                background: linear-gradient(180deg, #23457d 0%, #1d3968 100%);
                padding: 14px 22px;
                border-radius: 18px;
                font-weight: 900;
                border: 1px solid rgba(255,255,255,0.07);
                box-shadow: 0 6px 16px rgba(0,0,0,0.18);
            }}

            .cards-row {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 18px;
            }}

            .card-estado {{
                border-radius: 22px;
                padding: 20px 14px;
                min-height: 152px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                box-sizing: border-box;
                box-shadow:
                    0 10px 18px rgba(0,0,0,0.20),
                    inset 0 1px 0 rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.10);
            }}

            .card-numero {{
                font-size: 60px;
                font-weight: 900;
                color: white;
                line-height: 1;
                margin-bottom: 10px;
                text-shadow: 0 2px 6px rgba(0,0,0,0.12);
            }}

            .card-estado-nombre {{
                font-size: 22px;
                color: white;
                font-weight: 800;
                line-height: 1.15;
                text-shadow: 0 1px 3px rgba(0,0,0,0.10);
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

    components.html(html, height=580, scrolling=False)


# =========================================================
# CARGA ARCHIVO
# =========================================================
archivo = st.file_uploader("Sube archivo ETA", type=["xlsx", "xls"])

if archivo is not None:
    df = pd.read_excel(archivo, engine="openpyxl")

    columnas_necesarias = ["Estado", "Tipo Actividad", "Sub Tipo de Orden"]
    faltantes = [c for c in columnas_necesarias if c not in df.columns]

    if faltantes:
        st.error(f"Faltan estas columnas en el archivo: {', '.join(faltantes)}")
        st.stop()

    # Quitar almuerzos
    df = df[~df["Tipo Actividad"].astype(str).str.strip().isin([
        "Tiempo Almuerzo LU",
        "Tiempo de almuerzo"
    ])].copy()

    # Clasificar tecnología
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

    df["estado_visual"] = df["Estado"].apply(normalizar_estado)
    estados = ordenar_estados(list(df["estado_visual"].dropna().unique()))

    st.markdown(
        '<div class="titulo-dashboard">Dashboard de Instalaciones</div>',
        unsafe_allow_html=True
    )

    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    st.markdown(
        f'<div class="subtitulo-dashboard">Corte: {fecha} | Registros operativos: {len(df)}</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_bloque("GPON", df[df["tecnologia"] == "GPON"], estados)

    with col2:
        render_bloque("DTH", df[df["tecnologia"] == "DTH"], estados)

    no_clasificado = (df["tecnologia"] == "NO_CLASIFICADO").sum()
    st.markdown(
        f'<div class="no-clasificado">No clasificado: {no_clasificado}</div>',
        unsafe_allow_html=True
    )
