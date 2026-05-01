import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# =========================
# CONFIGURACIÓN
# =========================
st.set_page_config(
    page_title="Clasificación de Garantías",
    page_icon="📋",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CLASIFICACIONES = [
    "CALL CENTER",
    "CAMBIO DE EQUIPO",
    "CLIENTE",
    "DAÑO POR TERCEROS",
    "GARANTIA DE OTRA EMPRESA",
    "TECNICO",
    "VANDALISMO"
]

# =========================
# FUNCIONES
# =========================
def fecha_inicio_clasificacion():
    return date(2026, 4, 1)

@st.cache_data(ttl=60)
def cargar_garantias_pendientes():
    fecha_inicio = fecha_inicio_clasificacion().isoformat()

    response = (
        supabase
        .table("vista_garantias")
        .select("*")
        .eq("tipo_garantia", "INTERNA")
        .gte("fecha_garantia", fecha_inicio)
        .or_("clasificacion_garantia.is.null,clasificacion_garantia.eq.")
        .or_("comentario_supervisor.is.null,comentario_supervisor.eq.")
        .order("fecha_garantia", desc=False)
        .execute()
    )

    return pd.DataFrame(response.data or [])


def guardar_clasificacion(orden_trabajo, clasificacion, comentario):
    response = (
        supabase
        .table("kpi_ordenes_completadas")
        .update({
            "clasificacion_garantia": clasificacion,
            "comentario_supervisor": comentario
        })
        .eq("orden_trabajo", orden_trabajo)
        .execute()
    )
    return response


def filtro_checkbox(nombre, opciones, key_prefix):
    st.markdown(f"### {nombre}")

    if f"{key_prefix}_seleccion" not in st.session_state:
        st.session_state[f"{key_prefix}_seleccion"] = opciones.copy()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✓ Todo", key=f"{key_prefix}_todo"):
            st.session_state[f"{key_prefix}_seleccion"] = opciones.copy()
            for opcion in opciones:
                st.session_state[f"{key_prefix}_{opcion}"] = True
            st.rerun()

    with col2:
        if st.button("✕ Ninguno", key=f"{key_prefix}_ninguno"):
            st.session_state[f"{key_prefix}_seleccion"] = []
            for opcion in opciones:
                st.session_state[f"{key_prefix}_{opcion}"] = False
            st.rerun()

    seleccionados = []

    for opcion in opciones:
        checkbox_key = f"{key_prefix}_{opcion}"

        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = opcion in st.session_state[f"{key_prefix}_seleccion"]

        marcado = st.checkbox(
            opcion,
            key=checkbox_key
        )

        if marcado:
            seleccionados.append(opcion)

    st.session_state[f"{key_prefix}_seleccion"] = seleccionados

    return seleccionados

# =========================
# ENCABEZADO
# =========================
st.title("📋 Clasificación de Garantías Internas")

st.caption(
    f"Mostrando únicamente garantías internas pendientes desde el "
    f"{fecha_inicio_clasificacion().strftime('%d/%m/%Y')} en adelante."
)

df = cargar_garantias_pendientes()

if df.empty:
    st.success("✅ No hay garantías internas pendientes de clasificación.")
    st.stop()

# Evitar errores si algún supervisor viene vacío
df["supervisor_atendio"] = df["supervisor_atendio"].fillna("SIN SUPERVISOR")

# =========================
# FILTRO POR SUPERVISOR
# =========================
with st.sidebar:
    st.header("Filtros")

    supervisores = sorted(df["supervisor_atendio"].dropna().unique().tolist())

    supervisor_sel = filtro_checkbox(
        nombre="Supervisor",
        opciones=supervisores,
        key_prefix="filtro_supervisor"
    )

if supervisor_sel:
    df_filtrado = df[df["supervisor_atendio"].isin(supervisor_sel)].copy()
else:
    df_filtrado = df.iloc[0:0].copy()

# =========================
# KPIS
# =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Garantías pendientes", len(df_filtrado))

with col2:
    st.metric("Supervisores seleccionados", len(supervisor_sel))

with col3:
    st.metric("Técnicos con pendientes", df_filtrado["tecnico_causa_garantia"].nunique())

with col4:
    st.metric("Contratas con pendientes", df_filtrado["contrata_causa_garantia"].nunique())

st.divider()

# =========================
# LISTADO
# =========================
st.subheader("Garantías pendientes de clasificar")

st.info(
    "Seleccione una clasificación, escriba el comentario del supervisor y presione Guardar. "
    "Luego presione Aceptar para actualizar la lista."
)

if df_filtrado.empty:
    st.warning("No hay garantías pendientes para los supervisores seleccionados.")
    st.stop()

for _, row in df_filtrado.iterrows():
    orden = row.get("orden_trabajo", "")

    with st.expander(
        f"Orden {orden} | Cliente {row.get('numero_cliente', '')} | "
        f"Supervisor: {row.get('supervisor_atendio', '')} | "
        f"Causó: {row.get('tecnico_causa_garantia', '')} | "
        f"Cerró: {row.get('tecnico_atendio', '')}",
        expanded=False
    ):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.write("**Fecha garantía:**", row.get("fecha_garantia", ""))
            st.write("**Orden garantía:**", row.get("orden_trabajo", ""))
            st.write("**Cliente:**", row.get("numero_cliente", ""))

        with col2:
            st.write("**Orden causal:**", row.get("orden_anterior", ""))
            st.write("**Fecha causal:**", row.get("fecha_visita_causal", ""))
            st.write("**Días desde visita:**", row.get("dias_desde_visita", ""))

        with col3:
            st.write("**Supervisor que atendió:**", row.get("supervisor_atendio", ""))
            st.write("**Técnico que cerró:**", row.get("tecnico_atendio", ""))
            st.write("**Contrata que cerró:**", row.get("contrata_atendio", ""))
            st.write("**Tecnología:**", row.get("tecnologia", ""))

        with col4:
            st.write("**Técnico que causó:**", row.get("tecnico_causa_garantia", ""))
            st.write("**Contrata causal:**", row.get("contrata_causa_garantia", ""))
            st.write("**Sub tipo orden:**", row.get("sub_tipo_orden", ""))
            st.write("**Código completado:**", row.get("codigo_completado", ""))

        st.markdown("### Clasificación")

        clasificacion = st.selectbox(
            "Clasificación de garantía",
            [""] + CLASIFICACIONES,
            key=f"clasificacion_{orden}"
        )

        comentario = st.text_area(
            "Comentario del supervisor",
            key=f"comentario_{orden}",
            placeholder="Escriba el análisis o justificación de la clasificación..."
        )

        if st.button("💾 Guardar clasificación", key=f"guardar_{orden}"):

            if not clasificacion:
                st.warning("Debe seleccionar una clasificación.")

            elif not comentario.strip():
                st.warning("Debe escribir un comentario.")

            else:
                guardar_clasificacion(
                    orden_trabajo=orden,
                    clasificacion=clasificacion,
                    comentario=comentario.strip()
                )

                st.session_state["orden_guardada"] = orden

        if st.session_state.get("orden_guardada") == orden:
            st.success(f"✅ Garantía {orden} guardada correctamente.")

            if st.button("Aceptar", key=f"aceptar_{orden}"):
                st.session_state["orden_guardada"] = None
                st.cache_data.clear()
                st.rerun()