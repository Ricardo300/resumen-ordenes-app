import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================
st.set_page_config(
    page_title="Dashboard KPI ETA",
    layout="wide"
)

# ==========================================
# ESTILO COMPACTO
# ==========================================
st.markdown("""
<style>

h2 {
    font-size: 20px !important;
    margin-top: 10px !important;
}

h3 {
    font-size: 16px !important;
    margin-top: 5px !important;
}

.block-container {
    padding-top: 1rem;
}

div[data-testid="stMetricValue"] {
    font-size: 28px !important;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard KPI ETA")

# ==========================================
# BOTÓN ACTUALIZAR CACHE
# ==========================================
if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# SIDEBAR FILTROS
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
# FECHAS ISO (TIMESTAMP ROBUSTO)
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
# FUNCIÓN CON CACHE
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
# FILTROS MULTISELECT (DEFAULT TODOS)
# ==========================================
with st.sidebar:

    opciones_contrata = sorted(df["contrata"].dropna().unique())
    contrata = st.multiselect(
        "Contrata",
        opciones_contrata,
        default=opciones_contrata
    )

    opciones_tecnologia = sorted(df["tecnologia"].dropna().unique())
    tecnologia = st.multiselect(
        "Tecnología",
        opciones_tecnologia,
        default=opciones_tecnologia
    )

    opciones_tipo = sorted(df["tipo_actividad"].dropna().unique())
    tipo_actividad = st.multiselect(
        "Tipo Actividad",
        opciones_tipo,
        default=opciones_tipo
    )

# Aplicar filtros
df = df[
    df["tecnologia"].isin(tecnologia) &
    df["contrata"].isin(contrata) &
    df["tipo_actividad"].isin(tipo_actividad)
]

# ==========================================
# MÉTRICAS
# ==========================================
total_ordenes = len(df)
total_tecnicos = df["identificador_tecnico"].nunique()
dias_operativos = df["fecha"].nunique()
promedio_diario = round(total_ordenes / dias_operativos, 2) if dias_operativos else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("Órdenes", f"{total_ordenes:,}")
c2.metric("Técnicos", total_tecnicos)
c3.metric("Días Operativos", dias_operativos)
c4.metric("Promedio Día", promedio_diario)

# ==========================================
# GRÁFICO
# ==========================================
df["dia_mes"] = df["fecha"].dt.day

ordenes_dia = (
    df.groupby("dia_mes")["orden_trabajo"]
    .nunique()
    .reset_index(name="ordenes")
)

fig = px.bar(
    ordenes_dia,
    x="dia_mes",
    y="ordenes",
    text="ordenes"
)

fig.update_layout(height=300)
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

    st.dataframe(
        ordenes_provincia,
        use_container_width=True,
        height=300
    )

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

    df_prod["Productividad"] = (
        df_prod["Producción"] / df_prod["Dias_Trabajados"]
    ).round(2)

    df_prod = df_prod.drop(columns=["Dias_Trabajados"])
    df_prod = df_prod.sort_values("Producción", ascending=False)

    st.dataframe(
        df_prod,
        use_container_width=True,
        height=300
    )
