import streamlit as st
import pandas as pd
from datetime import datetime

# =========================================================
# CONFIGURACIÓN
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
}

.subtitulo-dashboard {
    font-size: 14px;
    color: #cbd5e1;
    margin-bottom: 20px;
}

.bloque-tec {
    background: #111827;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 15px;
}

.bloque-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
}

.bloque-titulo {
    font-size: 22px;
    font-weight: 800;
    color: white;
}

.bloque-total {
    font-size: 14px;
    color: #cbd5e1;
    background: #1f2937;
    padding: 5px 10px;
    border-radius: 10px;
}

.cards-row {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 10px;
}

.card-estado {
    border-radius: 15px;
    padding: 15px;
    text-align: center;
}

.card-numero {
    font-size: 30px;
    font-weight: 900;
    color: white;
}

.card-estado-nombre {
    font-size: 14px;
    color: white;
    font-weight: 600;
}

.no-clasificado {
    text-align: center;
    color: #cbd5e1;
    font-size: 15px;
    margin-top: 10px;
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
        "Pendiente": "#f59e0b",
        "Iniciado": "#eab308",
        "En ruta": "#3b82f6",
        "Suspendido": "#ef4444",
        "Completado": "#22c55e",
        "Cancelado": "#6b7280",
    }
    return colores.get(estado, "#64748b")


def render_bloque(nombre, df, estados):
    total = len(df)
    conteo = df["estado_visual"].value_counts().to_dict()

    cards = []
    for estado in estados:
        valor = conteo.get(estado, 0)
        color = color_estado(estado)

        cards.append(f"""
        <div class="card-estado" style="background:{color};">
            <div class="card-numero">{valor}</div>
            <div class="card-estado-nombre">{estado}</div>
        </div>
        """)

    cards_html = "".join(cards)

    st.markdown(f"""
    <div class="bloque-tec">
        <div class="bloque-header">
            <div class="bloque-titulo">{nombre}</div>
            <div class="bloque-total">Total {nombre}: {total}</div>
        </div>
        <div class="cards-row">
            {cards_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# CARGA ARCHIVO
# =========================================================
archivo = st.file_uploader("Sube archivo ETA", type=["xlsx", "xls"])

if archivo is not None:
    df = pd.read_excel(archivo, engine="openpyxl")

    # =====================================================
    # LIMPIEZA (QUITAR ALMUERZOS)
    # =====================================================
    df = df[~df["Tipo Actividad"].isin([
        "Tiempo Almuerzo LU",
        "Tiempo de almuerzo"
    ])].copy()

    # =====================================================
    # TECNOLOGÍA
    # =====================================================
    map_tecnologia = {
        "Cambio de Plan con Cambio de Equipo DTH": "DTH",
        "Equipo Adicional TV": "DTH",
        "Instalación de Cajas Adicionales DTH": "DTH",
        "Instalación de servicio televisión DTH": "DTH",
        "Instalación de TV (DTH)": "DTH",
        "Cambio de Equipo TV": "DTH",
        "Reparacion DTH": "DTH",
        "Reparacion Linea Fija LFI": "DTH",
        "Reparación servicio DTH": "DTH",

        "Cambio de Plan con Cambio de Equipo Datos y TV": "GPON",
        "Equipo Adicional Datos": "GPON",
        "Equipo Adicional Datos y TV": "GPON",
        "Instalacion Internet (GPON)": "GPON",
        "Reparación Internet (GPON)": "GPON",
    }

    df["tecnologia"] = df["Sub Tipo de Orden"].map(map_tecnologia)
    df["tecnologia"] = df["tecnologia"].fillna("NO_CLASIFICADO")

    # =====================================================
    # ESTADOS
    # =====================================================
    df["estado_visual"] = df["Estado"].apply(normalizar_estado)
    estados = ordenar_estados(df["estado_visual"].unique())

    # =====================================================
    # ENCABEZADO
    # =====================================================
    st.markdown('<div class="titulo-dashboard">Dashboard de Instalaciones</div>', unsafe_allow_html=True)

    fecha = datetime.now().strftime("%d/%m/%Y %I:%M %p")
    st.markdown(f'<div class="subtitulo-dashboard">Corte: {fecha} | Registros: {len(df)}</div>', unsafe_allow_html=True)

    # =====================================================
    # BLOQUES
    # =====================================================
    col1, col2 = st.columns(2)

    with col1:
        render_bloque("GPON", df[df["tecnologia"] == "GPON"], estados)

    with col2:
        render_bloque("DTH", df[df["tecnologia"] == "DTH"], estados)

    # =====================================================
    # NO CLASIFICADO
    # =====================================================
    no_clasificado = (df["tecnologia"] == "NO_CLASIFICADO").sum()

    st.markdown(f'<div class="no-clasificado">No clasificado: {no_clasificado}</div>', unsafe_allow_html=True)
