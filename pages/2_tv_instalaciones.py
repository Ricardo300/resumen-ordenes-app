import os
import time
import math
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="TV Instalaciones", layout="wide")

# =========================================================
# CONFIG GENERAL
# =========================================================
SEGUNDOS_POR_PANTALLA = 20
RUTA_ARCHIVO_FIJO = "/tmp/dashboard_eta_actual.xlsx"

# =========================================================
# ESTILO GENERAL
# =========================================================
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #050913 0%, #08101d 100%);
}

.main {
    background: transparent;
}

.block-container {
    padding-top: 0.2rem;
    padding-bottom: 0.5rem;
    max-width: 99%;
}

header, footer {
    visibility: hidden;
}

[data-testid="stHeader"] {
    display: none;
}

.titulo-dashboard {
    font-size: 42px;
    font-weight: 900;
    color: white;
    line-height: 1.05;
    margin-bottom: 4px;
}

.subtitulo-dashboard {
    font-size: 18px;
    color: #cbd5e1;
    margin-bottom: 10px;
    font-weight: 600;
}

.kpi-box {
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
    padding: 18px 14px;
    text-align: center;
    box-shadow: 0 12px 24px rgba(0,0,0,0.18);
}

.kpi-numero {
    font-size: 38px;
    font-weight: 900;
    color: white;
    line-height: 1;
    margin-bottom: 8px;
}

.kpi-titulo {
    font-size: 18px;
    font-weight: 800;
    color: #dbe7f5;
    line-height: 1.15;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNCIONES BASE
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


def render_kpi(titulo, valor, color_fondo="#0b1a34"):
    st.markdown(
        f"""
        <div class="kpi-box" style="background:{color_fondo};">
            <div class="kpi-numero">{valor}</div>
            <div class="kpi-titulo">{titulo}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# BLOQUE ESTADOS (PANTALLA 1 Y 2)
# =========================================================
def render_bloque_estados(nombre, df_bloque, estados):
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
                border-radius: 24px;
                padding: 22px;
                min-height: 540px;
                box-sizing: border-box;
                border: 1px solid rgba(255,255,255,0.07);
                box-shadow: 0 14px 28px rgba(0,0,0,0.22);
            }}
            .bloque-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            .bloque-titulo {{
                font-size: 38px;
                font-weight: 900;
                color: white;
            }}
            .bloque-total {{
                font-size: 22px;
                color: #f1f5f9;
                background: linear-gradient(180deg, #23457d 0%, #1d3968 100%);
                padding: 10px 18px;
                border-radius: 18px;
                font-weight: 900;
            }}
            .cards-row {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 16px;
            }}
            .card-estado {{
                border-radius: 20px;
                padding: 18px 12px;
                min-height: 138px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                box-sizing: border-box;
                box-shadow: 0 10px 18px rgba(0,0,0,0.20);
            }}
            .card-numero {{
                font-size: 54px;
                font-weight: 900;
                color: white;
                line-height: 1;
                margin-bottom: 8px;
            }}
            .card-estado-nombre {{
                font-size: 20px;
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
# GAUGE GRANDE (PANTALLA 1 Y 2)
# =========================================================
def polar_to_cartesian(cx, cy, r, angle_deg):
    angle_rad = math.radians(angle_deg)
    return (cx + r * math.cos(angle_rad), cy - r * math.sin(angle_rad))


def arc_points(cx, cy, r, start_deg, end_deg, steps=40):
    pts = []
    for i in range(steps + 1):
        ang = start_deg + (end_deg - start_deg) * i / steps
        x, y = polar_to_cartesian(cx, cy, r, ang)
        pts.append(f"{x:.2f},{y:.2f}")
    return " ".join(pts)


def needle_triangle(cx, cy, value, length=240, base_width=10):
    angle = 180 - (value * 180 / 100)
    angle_rad = math.radians(angle)

    tip_x = cx + length * math.cos(angle_rad)
    tip_y = cy - length * math.sin(angle_rad)

    px = math.sin(angle_rad)
    py = math.cos(angle_rad)

    left_x = cx - base_width * px
    left_y = cy - base_width * py
    right_x = cx + base_width * px
    right_y = cy + base_width * py

    return f"{left_x:.2f},{left_y:.2f} {right_x:.2f},{right_y:.2f} {tip_x:.2f},{tip_y:.2f}"


def render_gauge_tecnologia(df_bloque):
    conteo = df_bloque["estado_visual"].value_counts()

    completadas = int(conteo.get("Completado", 0))
    canceladas = int(conteo.get("Cancelado", 0))
    suspendidas = int(conteo.get("Suspendido", 0))
    total = len(df_bloque)

    numerador = completadas + canceladas + suspendidas
    cumplimiento = (numerador / total * 100) if total > 0 else 0

    width = 980
    height = 700
    cx = width / 2
    cy = 560
    radius = 340
    arc_thickness = 130

    segmentos = [
        (180, 150, "#dc2626"),
        (150, 120, "#f97316"),
        (120, 90,  "#facc15"),
        (90, 60,   "#86efac"),
        (60, 30,   "#22c55e"),
        (30, 0,    "#166534"),
    ]

    base_arc = arc_points(cx, cy, radius, 180, 0, steps=120)

    segmentos_svg = f'''
        <polyline points="{base_arc}"
                  fill="none"
                  stroke="rgba(255,255,255,0.05)"
                  stroke-width="{arc_thickness}"
                  stroke-linecap="butt"
                  stroke-linejoin="round" />
    '''

    for start_deg, end_deg, color in segmentos:
        pts = arc_points(cx, cy, radius, start_deg, end_deg, steps=30)
        segmentos_svg += f'''
            <polyline points="{pts}"
                      fill="none"
                      stroke="{color}"
                      stroke-width="{arc_thickness}"
                      stroke-linecap="butt"
                      stroke-linejoin="round" />
        '''

    ticks = [0, 17, 33, 50, 67, 83, 100]
    ticks_svg = ""
    for t in ticks:
        angle = 180 - (t * 180 / 100)
        x1, y1 = polar_to_cartesian(cx, cy, radius + arc_thickness/2 + 4, angle)
        x2, y2 = polar_to_cartesian(cx, cy, radius + arc_thickness/2 + 20, angle)
        xt, yt = polar_to_cartesian(cx, cy, radius + arc_thickness/2 + 46, angle)

        ticks_svg += f'''
            <line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"
                  stroke="white" stroke-width="3" />
            <text x="{xt:.2f}" y="{yt:.2f}" fill="white" font-size="22"
                  font-weight="700" text-anchor="middle" dominant-baseline="middle">{t}</text>
        '''

    needle_points = needle_triangle(cx, cy, cumplimiento, length=245, base_width=10)

    svg_html = f"""
    <div style="width:100%; display:flex; justify-content:center; align-items:center;">
        <svg viewBox="0 0 {width} {height}" width="100%" height="640" style="overflow:visible;">
            <text x="{cx}" y="92" fill="white" font-size="72" font-weight="800" text-anchor="middle">
                {cumplimiento:.1f}%
            </text>

            {segmentos_svg}
            {ticks_svg}

            <polygon points="{needle_points}" fill="#f8fafc" stroke="#e2e8f0" stroke-width="2" />
            <circle cx="{cx}" cy="{cy}" r="28" fill="#d1d5db" stroke="white" stroke-width="5" />
        </svg>
    </div>
    """
    components.html(svg_html, height=650, scrolling=False)

# =========================================================
# PANTALLA 1 Y PANTALLA 2
# PANTALLA 1 = GPON
# PANTALLA 2 = DTH
# =========================================================
def render_pantalla_tecnologia(df_bloque, nombre_pantalla, estados):
    st.markdown(
        f'<div class="titulo-dashboard">{nombre_pantalla}</div>',
        unsafe_allow_html=True
    )

    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    st.markdown(
        f'<div class="subtitulo-dashboard">Corte: {fecha}</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1.0, 1.35], gap="large")

    with col1:
        render_bloque_estados(nombre_pantalla, df_bloque, estados)

    with col2:
        render_gauge_tecnologia(df_bloque)

# =========================================================
# PANTALLA 3 = BACKOFFICE
# =========================================================
def render_pantalla_backoffice(df):
    mapa_bo = {
        # Andres Corea
        "CAR567": "Andres Corea",
        "CAR566": "Andres Corea",
        "CAR453": "Andres Corea",
        "CAR396": "Andres Corea",
        "CAR397": "Andres Corea",
        "CAR439": "Andres Corea",
        "CAR508": "Andres Corea",
        "GCAR513": "Andres Corea",
        "GCAR603": "Andres Corea",
        "GCAR968": "Andres Corea",
        "GCAR351": "Andres Corea",
        "GCAR627": "Andres Corea",
        "GCAR1001": "Andres Corea",
        "GCAR1008": "Andres Corea",
        "GCAR1016": "Andres Corea",
        "GCAR1019": "Andres Corea",
        "GCAR1020": "Andres Corea",
        "GCAR1035": "Andres Corea",
        "GCAR1037": "Andres Corea",

        # Adriana Rojas
        "CAR270": "Adriana Rojas",
        "CAR1002": "Adriana Rojas",
        "CAR040": "Adriana Rojas",
        "CAR455": "Adriana Rojas",
        "CAR285": "Adriana Rojas",
        "GCAR780": "Adriana Rojas",
        "GCAR606": "Adriana Rojas",
        "GCAR593": "Adriana Rojas",
        "GCAR554": "Adriana Rojas",
        "GCAR551": "Adriana Rojas",
        "GCAR506": "Adriana Rojas",
        "GCAR860": "Adriana Rojas",
        "GCAR953": "Adriana Rojas",
        "GCAR951": "Adriana Rojas",
        "GCAR840": "Adriana Rojas",
        "GCAR670": "Adriana Rojas",
        "GCAR964": "Adriana Rojas",
        "GCAR103": "Adriana Rojas",
        "GCAR869": "Adriana Rojas",
        "GCAR105": "Adriana Rojas",
        "GCAR184": "Adriana Rojas",
        "GCAR1033": "Adriana Rojas",
        "GCAR1048": "Adriana Rojas",

        # Sofia Alvarez
        "CAR261": "Sofia Alvarez",
        "CAR395": "Sofia Alvarez",
        "CAR259": "Sofia Alvarez",
        "CAR365": "Sofia Alvarez",
        "CAR321": "Sofia Alvarez",
        "CAR507": "Sofia Alvarez",
        "GCAR1001": "Sofia Alvarez",
        "GCAR923": "Sofia Alvarez",
        "GCAR822": "Sofia Alvarez",
        "GCAR798": "Sofia Alvarez",
        "GCAR608": "Sofia Alvarez",
        "GCAR604": "Sofia Alvarez",
        "GCAR570": "Sofia Alvarez",
        "GCAR491": "Sofia Alvarez",
        "GCAR935": "Sofia Alvarez",
        "GCAR880": "Sofia Alvarez",
        "GCAR946": "Sofia Alvarez",
        "GCAR956": "Sofia Alvarez",
        "GCAR990": "Sofia Alvarez",
        "GCAR986": "Sofia Alvarez",
        "GCAR978": "Sofia Alvarez",
        "GCAR1003": "Sofia Alvarez",
        "GCAR1024": "Sofia Alvarez",
        "GCAR996": "Sofia Alvarez",
        "GCAR789": "Sofia Alvarez",

        # Harold Castillo
        "GCAR906": "Harold Castillo",
        "GCAR796": "Harold Castillo",
        "GCAR585": "Harold Castillo",
        "GCAR583": "Harold Castillo",
        "GCAR955": "Harold Castillo",
        "GCAR817": "Harold Castillo",
        "GCAR991": "Harold Castillo",
        "GCAR883": "Harold Castillo",
        "GCAR887": "Harold Castillo",
        "GCAR0345": "Harold Castillo",
        "GCAR886": "Harold Castillo",
        "GCAR2378": "Harold Castillo",
        "GCAR349": "Harold Castillo",
        "GCAR253": "Harold Castillo",
        "GCAR329": "Harold Castillo",
        "GCAR1006": "Harold Castillo",
        "GCAR1010": "Harold Castillo",
        "GCAR1015": "Harold Castillo",
        "GCAR963": "Harold Castillo",
        "GCAR781": "Harold Castillo",
        "GCAR1029": "Harold Castillo",
        "GCAR1028": "Harold Castillo",
        "GCAR1034": "Harold Castillo",
        "GCAR1025": "Harold Castillo",
        "GCAR1043": "Harold Castillo",
        "GCAR1022": "Harold Castillo",
        "GCAR1039": "Harold Castillo",
        "GCAR1027": "Harold Castillo",
    }

    if "Identificador Tecnico" not in df.columns:
        st.error("No existe la columna 'Identificador Tecnico' en el archivo.")
        return

    df_bo = df.copy()

    df_bo["Identificador Tecnico"] = (
        df_bo["Identificador Tecnico"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df_bo["backoffice"] = df_bo["Identificador Tecnico"].map(mapa_bo).fillna("Sin-Asignar")

    # -----------------------------------------
    # ESTATUS DE LA BOLSA
    # -----------------------------------------
    conteo_estados = df_bo["estado_visual"].value_counts()

    pendientes = int(conteo_estados.get("Pendiente", 0))
    iniciados = int(conteo_estados.get("Iniciado", 0))
    en_ruta = int(conteo_estados.get("En ruta", 0))
    suspendidos = int(conteo_estados.get("Suspendido", 0))
    completados = int(conteo_estados.get("Completado", 0))
    cancelados = int(conteo_estados.get("Cancelado", 0))

    # Fila de estatus
    c1, c2, c3, c4, c5, c6 = st.columns(6, gap="medium")
    with c1:
        render_kpi("Pendiente", pendientes, "#f4a300")
    with c2:
        render_kpi("Iniciado", iniciados, "#d9ad00")
    with c3:
        render_kpi("En ruta", en_ruta, "#3f83f8")
    with c4:
        render_kpi("Suspendido", suspendidos, "#ef4444")
    with c5:
        render_kpi("Completado", completados, "#22c55e")
    with c6:
        render_kpi("Cancelado", cancelados, "#7b8496")

    # -----------------------------------------
    # ALERTA SIN ASIGNAR (SEPARADA)
    # -----------------------------------------
    sin_asignar_total = int((df_bo["backoffice"] == "Sin-Asignar").sum())

    color_alerta = "#dc2626" if sin_asignar_total > 0 else "#16a34a"
    icono_alerta = "🚨" if sin_asignar_total > 0 else "✅"

    st.markdown(
        f"""
        <div style="
            margin-top: 14px;
            margin-bottom: 18px;
            width: 380px;
            margin-left: auto;
            margin-right: auto;
            background: {color_alerta};
            color: white;
            border-radius: 18px;
            padding: 14px 18px;
            text-align: center;
            font-size: 24px;
            font-weight: 900;
            box-shadow: 0 12px 24px rgba(0,0,0,0.20);
        ">
            {icono_alerta} Sin asignar: {sin_asignar_total}
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------
    # RANKING POR BACKOFFICE (CUMPLIMIENTO)
    # -----------------------------------------
    estados_pendientes = ["Pendiente", "Iniciado", "En ruta"]
    
    df_bo["es_pendiente"] = df_bo["estado_visual"].isin(estados_pendientes).astype(int)
    df_bo["es_completada"] = (df_bo["estado_visual"] == "Completado").astype(int)
    df_bo["es_suspendida"] = (df_bo["estado_visual"] == "Suspendido").astype(int)
    df_bo["es_cancelada"] = (df_bo["estado_visual"] == "Cancelado").astype(int)
    
    df_rank = df_bo[df_bo["backoffice"] != "Sin-Asignar"].copy()
    
    if df_rank.empty:
        st.warning("No hay órdenes con BackOffice asignado para mostrar.")
        return
    
    # -----------------------------
    # AGRUPACIÓN
    # -----------------------------
    resumen = (
        df_rank.groupby("backoffice", as_index=False)
        .agg(
            total_ordenes=("estado_visual", "count"),
            completadas=("es_completada", "sum"),
            pendientes=("es_pendiente", "sum"),
            suspendidas=("es_suspendida", "sum"),
            canceladas=("es_cancelada", "sum"),
        )
    )
    
    # -----------------------------
    # CALCULO CUMPLIMIENTO
    # -----------------------------
    resumen["gestionadas"] = (
        resumen["completadas"]
        + resumen["suspendidas"]
        + resumen["canceladas"]
    )
    
    resumen["pct_cumplimiento"] = resumen.apply(
        lambda x: x["gestionadas"] / x["total_ordenes"] if x["total_ordenes"] > 0 else 0,
        axis=1
    )
    
    # ordenar (mejor primero)
    resumen = resumen.sort_values(
        ["pct_cumplimiento", "pendientes"],
        ascending=[False, True]
    ).reset_index(drop=True)
    
    # -----------------------------
    # HTML RENDER
    # -----------------------------
    filas_html = ""
    for idx, row in resumen.iterrows():
        porcentaje = row["pct_cumplimiento"] * 100
    
        # colores según cumplimiento
        if porcentaje >= 90:
            color_barra = "#22c55e"  # verde
        elif porcentaje >= 75:
            color_barra = "#f59e0b"  # naranja
        else:
            color_barra = "#ef4444"  # rojo
    
        ancho_barra = max(6, min(100, porcentaje))
    
        filas_html += f"""
        <div class="fila-bo">
            <div class="bo-pos">{idx + 1}</div>
            <div class="bo-nombre">{row['backoffice']}</div>
            <div class="bo-completadas">{int(row['completadas'])} completadas</div>
            <div class="bo-pendientes">{int(row['pendientes'])} pendientes</div>
            <div class="barra-wrap">
                <div class="barra-fondo">
                    <div class="barra-fill" style="width:{ancho_barra}%; background:{color_barra};"></div>
                </div>
            </div>
            <div class="bo-pct">{porcentaje:.1f}%</div>
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
            .contenedor {{
                background: linear-gradient(180deg, #0b1a34 0%, #0a1730 100%);
                border-radius: 24px;
                padding: 22px;
                min-height: 500px;
                border: 1px solid rgba(255,255,255,0.07);
                box-shadow: 0 14px 28px rgba(0,0,0,0.22);
            }}
            .titulo-tabla {{
                color: white;
                font-size: 28px;
                font-weight: 900;
                margin-bottom: 16px;
            }}
            .fila-bo {{
                display: grid;
                grid-template-columns: 60px 1.3fr 1fr 1fr 1.4fr 110px;
                align-items: center;
                gap: 12px;
                background: #12264d;
                border-radius: 18px;
                padding: 16px 18px;
                margin-bottom: 12px;
            }}
            .bo-pos {{
                font-size: 28px;
                font-weight: 900;
                color: white;
                text-align: center;
            }}
            .bo-nombre {{
                font-size: 24px;
                font-weight: 900;
                color: white;
            }}
            .bo-completadas {{
                font-size: 20px;
                font-weight: 800;
                color: #22c55e;
                text-align: center;
            }}
            .bo-pendientes {{
                font-size: 20px;
                font-weight: 800;
                color: #f59e0b;
                text-align: center;
            }}
            .barra-wrap {{
                width: 100%;
            }}
            .barra-fondo {{
                width: 100%;
                height: 26px;
                background: #243b63;
                border-radius: 999px;
                overflow: hidden;
                box-shadow: inset 0 2px 6px rgba(0,0,0,0.35);
            }}
            .barra-fill {{
                height: 100%;
                border-radius: 999px;
            }}
            .bo-pct {{
                font-size: 28px;
                font-weight: 900;
                color: white;
                text-align: right;
            }}
        </style>
    </head>
    <body>
        <div class="contenedor">
            <div class="titulo-tabla">Cumplimiento por BackOffice</div>
            {filas_html}
        </div>
    </body>
    </html>
    """
    
    components.html(html, height=560, scrolling=False)
    # =========================================
    # DEBUG - TABLA DE VALIDACIÓN
    # =========================================
    st.markdown("### 🔍 Validación de clasificación (debug)")
    
    df_debug = df_bo.copy()
    
    # Opcional: si tienes columna de orden, inclúyela
    columnas_debug = []
    
    if "Orden de Trabajo" in df_debug.columns:
        columnas_debug.append("Orden de Trabajo")
    
    columnas_debug += [
        "Identificador Tecnico",
        "backoffice",
        "Estado",
        "estado_visual"
    ]
    
    df_debug = df_debug[columnas_debug].copy()
    
    # Mostrar solo los que están sin asignar primero (para enfocarnos)
    st.markdown("#### 🚨 Registros SIN ASIGNAR")
    st.dataframe(
        df_debug[df_debug["backoffice"] == "Sin-Asignar"].head(1000),
        use_container_width=True
    )
    
    # Mostrar muestra general
    st.markdown("#### 📊 Muestra general")
    st.dataframe(
        df_debug.head(1000),
        use_container_width=True
    )
    # =========================================
    # DEBUG - VALIDACIÓN DIRECTA CON ESTADO
    # =========================================
    st.markdown("### 🔎 Validación por BackOffice usando columna Estado")
    
    tabla_bo_estado = (
        df_bo.groupby(["backoffice", "Estado"], as_index=False)
        .size()
        .rename(columns={"size": "cantidad"})
        .sort_values(["backoffice", "Estado"])
    )
    
    st.dataframe(tabla_bo_estado, use_container_width=True)
    
    st.markdown("### 🔎 Pendientes por BackOffice (Pendiente + Iniciado + En ruta)")
    
    tabla_pendientes_bo = (
        df_bo[df_bo["Estado"].isin(["Pendiente", "Iniciado", "En ruta"])]
        .groupby(["backoffice", "Estado"], as_index=False)
        .size()
        .rename(columns={"size": "cantidad"})
        .sort_values(["backoffice", "Estado"])
    )
    
    st.dataframe(tabla_pendientes_bo, use_container_width=True)
# =========================================================
# VALIDAR ARCHIVO
# =========================================================
if not os.path.exists(RUTA_ARCHIVO_FIJO):
    st.warning("No hay archivo cargado. Ve a la página 'Cargar Archivo' y sube el Excel.")
    st.stop()

# =========================================================
# AUTO REFRESH
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
# LEER EXCEL
# =========================================================
df = pd.read_excel(RUTA_ARCHIVO_FIJO, engine="openpyxl")
df.columns = df.columns.str.strip()

columnas_necesarias = ["Estado", "Tipo Actividad", "Sub Tipo de Orden", "Identificador Tecnico"]
faltantes = [c for c in columnas_necesarias if c not in df.columns]
if faltantes:
    st.error(f"Faltan estas columnas en el archivo: {', '.join(faltantes)}")
    st.stop()

df = df[~df["Tipo Actividad"].astype(str).str.strip().isin([
    "Tiempo Almuerzo LU",
    "Tiempo de almuerzo"
])].copy()

# =========================================================
# MAPEO TECNOLOGÍA
# =========================================================
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
estados_visibles = [
    e for e in estados
    if e in ["Pendiente", "Iniciado", "En ruta", "Suspendido", "Completado", "Cancelado"]
]

# =========================================================
# DATA POR PANTALLA
# =========================================================
df_gpon = df[df["tecnologia"] == "GPON"].copy()
df_dth = df[df["tecnologia"] == "DTH"].copy()

# =========================================================
# ROTACIÓN DE PANTALLAS
# PANTALLA 1 = GPON
# PANTALLA 2 = DTH
# PANTALLA 3 = BACKOFFICE
# =========================================================
pantalla_actual = int(time.time() / SEGUNDOS_POR_PANTALLA) % 3 + 1

if pantalla_actual == 1:
    render_pantalla_tecnologia(df_gpon, "GPON", estados_visibles)

elif pantalla_actual == 2:
    render_pantalla_tecnologia(df_dth, "DTH", estados_visibles)

else:
    render_pantalla_backoffice(df)
