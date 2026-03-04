import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Dashboard KPI ETA", layout="wide")

# ==========================================
# ESTILO COMPACTO
# ==========================================
st.markdown("""
<style>
h2 { font-size: 20px !important; margin-top: 10px !important; }
h3 { font-size: 16px !important; margin-top: 5px !important; }
.block-container { padding-top: 1rem; }
div[data-testid="stMetricValue"] { font-size: 28px !important; }

/* botones un poco más compactos */
div.stButton > button {
    padding: 0.25rem 0.55rem !important;
    font-size: 0.80rem !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard KPI")

# ==========================================
# BOTÓN ACTUALIZAR
# ==========================================
if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# SIDEBAR PERIODO
# ==========================================
with st.sidebar:
    st.markdown("## 🎛 Filtros")

    año = st.selectbox("Año", [2026, 2025, 2024], index=0)

    meses_dict = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
        "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
        "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
    }

    mes_nombre = st.selectbox(
        "Mes",
        list(meses_dict.keys()),
        index=datetime.now().month - 1
    )
    mes = meses_dict[mes_nombre]

# ==========================================
# FECHAS ISO (TIMESTAMP)
# ==========================================
primer_dia = f"{año}-{mes:02d}-01T00:00:00"

if mes == 12:
    siguiente_mes = 1
    siguiente_año = año + 1
else:
    siguiente_mes = mes + 1
    siguiente_año = año

primer_dia_siguiente = f"{siguiente_año}-{siguiente_mes:02d}-01T00:00:00"

st.markdown(f"**📅 Periodo Analizado:** {mes_nombre} {año}")

# ==========================================
# CONEXIÓN SUPABASE
# ==========================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ==========================================
# OBTENER DATOS
# ==========================================
@st.cache_data(ttl=300)
def obtener_datos(inicio, fin):
    todos = []
    limite = 1000
    offset = 0

    while True:
        response = (
            supabase
            .table("kpi_ordenes_completadas")
            .select("*")
            .gte("fecha", inicio)
            .lt("fecha", fin)
            .range(offset, offset + limite - 1)
            .execute()
        )

        data = response.data
        if not data:
            break

        todos.extend(data)

        if len(data) < limite:
            break

        offset += limite

    return todos

data = obtener_datos(primer_dia, primer_dia_siguiente)

if not data:
    st.warning("No hay datos para el período seleccionado.")
    st.stop()

df = pd.DataFrame(data)
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

# ==========================================
# FILTRO CHECKBOX + BOTONES TODO/NINGUNO (FUNCIONAL)
# ==========================================
def filtro_checkbox(label, opciones, key_prefix):
    with st.sidebar.expander(label, expanded=False):

        col1, col2 = st.columns(2)

        # ✓ Todo
        if col1.button("✓ Todo", key=f"{key_prefix}_all", type="secondary"):
            for opcion in opciones:
                st.session_state[f"{key_prefix}_{opcion}"] = True

        # ✕ Ninguno
        if col2.button("✕ Ninguno", key=f"{key_prefix}_none", type="secondary"):
            for opcion in opciones:
                st.session_state[f"{key_prefix}_{opcion}"] = False

        seleccionados = []

        for opcion in opciones:
            # Inicializar estado
            if f"{key_prefix}_{opcion}" not in st.session_state:
                st.session_state[f"{key_prefix}_{opcion}"] = True

            estado = st.checkbox(opcion, key=f"{key_prefix}_{opcion}")
            if estado:
                seleccionados.append(opcion)

    return seleccionados

# Opciones dinámicas
opciones_contrata = sorted(df["contrata"].dropna().unique())
opciones_tecnologia = sorted(df["tecnologia"].dropna().unique())
opciones_tipo = sorted(df["tipo_actividad"].dropna().unique())

contrata = filtro_checkbox("Contrata", opciones_contrata, "con")
tecnologia = filtro_checkbox("Tecnología", opciones_tecnologia, "tec")
tipo_actividad = filtro_checkbox("Tipo Actividad", opciones_tipo, "tip")

# Aplicar filtros
df = df[
    df["tecnologia"].isin(tecnologia) &
    df["contrata"].isin(contrata) &
    df["tipo_actividad"].isin(tipo_actividad)
]

# Si te quedas sin selección (todo en falso), evita error y muestra aviso
if df.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ==========================================
# MÉTRICAS
# ==========================================
total_ordenes = len(df)
total_tecnicos = df["identificador_tecnico"].nunique()
dias_operativos = df["fecha"].nunique()
promedio_diario = round(total_ordenes / dias_operativos, 2) if dias_operativos else 0
total_garantias = len(df[df["garantia"].astype(str).str.strip().str.upper() == "SI"])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Órdenes", f"{total_ordenes:,}")
c2.metric("Técnicos", total_tecnicos)
c3.metric("Días Operativos", dias_operativos)
c4.metric("Promedio Día", promedio_diario)
c5.metric("Garantías", total_garantias)

# ==========================================
# GRÁFICO (COLORES DINÁMICOS)
# ==========================================
df["dia_mes"] = df["fecha"].dt.day

ordenes_dia = (
    df.groupby("dia_mes")["orden_trabajo"]
    .nunique()
    .reset_index(name="ordenes")
    .sort_values("dia_mes")
)

fig = px.bar(
    ordenes_dia,
    x="dia_mes",
    y="ordenes",
    text="ordenes",
    color="ordenes",
    color_continuous_scale="Blues"
)

fig.update_layout(height=320, coloraxis_showscale=False)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TABLAS
# ==========================================
st.markdown("### 📋 Detalle Operativo")

col_tab1, col_tab2 = st.columns([1, 2])

with col_tab1:
    st.markdown("#### 📍 Órdenes por Provincia")
    ordenes_provincia = (
        df.groupby("provincia")["orden_trabajo"]
        .nunique()
        .reset_index(name="Órdenes")
        .sort_values("Órdenes", ascending=False)
    )
    st.dataframe(ordenes_provincia, use_container_width=True, height=300)

with col_tab2:
    st.markdown("#### 👷 Producción y Productividad por Técnico")
    df_prod = (
        df.groupby(["identificador_tecnico", "contrata"])
        .agg(
            Producción=("orden_trabajo", "count"),
            Dias_Trabajados=("fecha", "nunique")
        )
        .reset_index()
    )
    df_prod["Productividad"] = (df_prod["Producción"] / df_prod["Dias_Trabajados"]).round(2)
    df_prod = df_prod.drop(columns=["Dias_Trabajados"]).sort_values("Producción", ascending=False)
    st.dataframe(df_prod, use_container_width=True, height=300)
#================================================
#  GRAFICO CUMPLIMIENTO META 4 ORDENES
#================================================
st.subheader("Promedio de Órdenes por Técnico por Contrata")

# asegurar formato fecha
df["fecha"] = pd.to_datetime(df["fecha"])

# contar órdenes por técnico por día
ordenes_tecnico = (
    df.groupby(["fecha", "contrata", "identificador_tecnico"])
      .size()
      .reset_index(name="ordenes")
)

# calcular promedio por contrata
promedio_contrata = (
    ordenes_tecnico.groupby("contrata")["ordenes"]
      .mean()
      .reset_index()
)

# ordenar de mayor a menor
promedio_contrata = promedio_contrata.sort_values("ordenes", ascending=False)

# crear gráfico
fig = px.bar(
    promedio_contrata,
    x="contrata",
    y="ordenes",
    text_auto=".2f"
)

# colores alternados
colors = ["#1565C0" if i % 2 == 0 else "#90CAF9" for i in range(len(promedio_contrata))]

fig.update_traces(
    marker_color=colors,
    width=0.6
)

# reducir espacio entre barras
fig.update_layout(bargap=0.15)

# línea meta
fig.add_hline(
    y=4,
    line_dash="dash",
    line_color="red",
    annotation_text="Meta 4 órdenes",
    annotation_position="top right"
)

# apariencia
fig.update_layout(
    showlegend=False,
    xaxis_title="Contrata",
    yaxis_title="Órdenes promedio",
    xaxis_tickangle=-90,
    template="plotly_dark",
    margin=dict(b=120)
)

# mostrar gráfico (con key para evitar duplicados)
st.plotly_chart(
    fig,
    use_container_width=True,
    key="grafico_productividad_contrata"
)
