import os
import time
from io import BytesIO
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Dashboard de Instalaciones", layout="wide")

# =========================================================
# CONFIG
# =========================================================
SEGUNDOS_POR_PANTALLA = 12
RUTA_ARCHIVO_FIJO = "/tmp/dashboard_eta_actual.xlsx"

# =========================================================
# ESTILO GENERAL
# =========================================================
st.markdown("""
<style>
:root {
    --text-main: #ffffff;
    --text-soft: #cbd5e1;
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

.kpi-box {
    background: linear-gradient(180deg, #0b1a34 0%, #0a1730 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
    padding: 22px 18px;
    text-align: center;
    box-shadow: 0 12px 24px rgba(0,0,0,0.18);
}

.kpi-numero {
    font-size: 48px;
    font-weight: 900;
    color: white;
    line-height: 1;
    margin-bottom: 10px;
}

.kpi-titulo {
    font-size: 22px;
    font-weight: 800;
    color: #dbe7f5;
    line-height: 1.15;
}

.pantalla-badge {
    display: inline-block;
    font-size: 18px;
    font-weight: 800;
    color: #dbe7f5;
    background: #183153;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 8px 14px;
    margin-bottom: 14px;
}

.archivo-info {
    font-size: 16px;
    color: #dbe7f5;
    margin-bottom: 10px;
    font-weight: 700;
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


def render_kpi(titulo, valor):
    st.markdown(
        f"""
        <div class="kpi-box">
            <div class="kpi-numero">{valor}</div>
            <div class="kpi-titulo">{titulo}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_pantalla_1(df, estados):
    st.markdown('<div class="pantalla-badge">Pantalla 1</div>', unsafe_allow_html=True)
    st.markdown('<div class="titulo-dashboard">Dashboard de Instalaciones</div>', unsafe_allow_html=True)

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
#================================================
#PLANTA 2"
#================================================
def render_pantalla_2(df):
    import math

    st.markdown('<div class="pantalla-badge">Pantalla 2</div>', unsafe_allow_html=True)
    st.markdown('<div class="titulo-dashboard">% Cumplimiento de Ruta</div>', unsafe_allow_html=True)

    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    st.markdown(
        f'<div class="subtitulo-dashboard">Corte: {fecha}</div>',
        unsafe_allow_html=True
    )

    conteo = df["estado_visual"].value_counts()

    completadas = int(conteo.get("Completado", 0))
    canceladas = int(conteo.get("Cancelado", 0))
    suspendidas = int(conteo.get("Suspendido", 0))
    total = len(df)

    numerador = completadas + canceladas + suspendidas
    cumplimiento = (numerador / total * 100) if total > 0 else 0

    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=cumplimiento,
        title={
            "text": f"{cumplimiento:.1f}%",
            "font": {"size": 64, "color": "white"}
        },
        gauge={
            "shape": "angular",
            "axis": {
                "range": [0, 100],
                "tickmode": "array",
                "tickvals": [0, 16.7, 33.3, 50, 66.7, 83.3, 100],
                "ticktext": ["0", "17", "33", "50", "67", "83", "100"],
                "tickwidth": 2,
                "tickcolor": "white",
                "tickfont": {"size": 16, "color": "white"}
            },
            "bar": {
                "color": "rgba(0,0,0,0)",
                "thickness": 0.18
            },
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 16.7], "color": "#dc2626"},
                {"range": [16.7, 33.3], "color": "#f97316"},
                {"range": [33.3, 50], "color": "#facc15"},
                {"range": [50, 66.7], "color": "#86efac"},
                {"range": [66.7, 83.3], "color": "#22c55e"},
                {"range": [83.3, 100], "color": "#166534"}
            ],
            "threshold": {
                "line": {"color": "rgba(0,0,0,0)", "width": 0},
                "thickness": 0,
                "value": cumplimiento
            }
        }
    ))

    # Centro real aproximado del semicírculo en coordenadas paper
    cx, cy = 0.5, 0.19

    # 0% = izquierda, 50% = arriba, 100% = derecha
    angle_deg = 180 - (cumplimiento * 180 / 100)
    angle = math.radians(angle_deg)

    # Largo de aguja
    needle_len = 0.34

    # Punta
    tip_x = cx + needle_len * math.cos(angle)
    tip_y = cy + needle_len * math.sin(angle)

    # Base triangular
    base_radius = 0.035
    base_half_width = 0.010

    bx = cx + base_radius * math.cos(angle)
    by = cy + base_radius * math.sin(angle)

    px = -math.sin(angle)
    py = math.cos(angle)

    left_x = cx + base_half_width * px
    left_y = cy + base_half_width * py
    right_x = cx - base_half_width * px
    right_y = cy - base_half_width * py

    path = f"M {left_x},{left_y} L {right_x},{right_y} L {tip_x},{tip_y} Z"

    fig.add_shape(
        type="path",
        path=path,
        fillcolor="#f8fafc",
        line=dict(color="#f8fafc", width=1),
        xref="paper",
        yref="paper",
        layer="above"
    )

    fig.add_shape(
        type="circle",
        x0=cx - 0.020, y0=cy - 0.020,
        x1=cx + 0.020, y1=cy + 0.020,
        fillcolor="#e5e7eb",
        line=dict(color="white", width=2),
        xref="paper",
        yref="paper",
        layer="above"
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=560,
        margin=dict(l=30, r=30, t=90, b=10),
        font={"color": "white"},
    )

    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4, gap="large")
    with c1:
        render_kpi("Completadas", completadas)
    with c2:
        render_kpi("Suspendidas", suspendidas)
    with c3:
        render_kpi("Canceladas", canceladas)
    with c4:
        render_kpi("Total Ruta", total)
# =========================================================
# UPLOADER
# =========================================================
archivo = st.file_uploader("Sube archivo ETA", type=["xlsx", "xls"])

if archivo is not None:
    with open(RUTA_ARCHIVO_FIJO, "wb") as f:
        f.write(archivo.getvalue())
    st.success(f"Archivo guardado: {archivo.name}")

if not os.path.exists(RUTA_ARCHIVO_FIJO):
    st.stop()

st.markdown(
    f'<div class="archivo-info">Archivo activo: {os.path.basename(RUTA_ARCHIVO_FIJO)}</div>',
    unsafe_allow_html=True
)

# =========================================================
# AUTO-REFRESH
# =========================================================
components.html(
    f"""
    <script>
        setTimeout(function() {{
            window.parent.location.reload();
        }}, {SEGUNDOS_POR_PANTALLA * 1000});
    </script>
    """,
    height=0,
)

# =========================================================
# LEER ARCHIVO GUARDADO
# =========================================================
df = pd.read_excel(RUTA_ARCHIVO_FIJO, engine="openpyxl")

columnas_necesarias = ["Estado", "Tipo Actividad", "Sub Tipo de Orden"]
faltantes = [c for c in columnas_necesarias if c not in df.columns]

if faltantes:
    st.error(f"Faltan estas columnas en el archivo: {', '.join(faltantes)}")
    st.stop()

df = df[~df["Tipo Actividad"].astype(str).str.strip().isin([
    "Tiempo Almuerzo LU",
    "Tiempo de almuerzo"
])].copy()

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

# =========================================================
# PANTALLA ACTUAL
# =========================================================
pantalla_actual = int(time.time() / SEGUNDOS_POR_PANTALLA) % 2 + 1

if pantalla_actual == 1:
    render_pantalla_1(df, estados)
else:
    render_pantalla_2(df)
