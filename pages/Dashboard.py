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

st.title("📊 Dashboard KPI ETA")

# ==========================================
# BOTÓN ACTUALIZAR CACHE
# ==========================================
if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.success("Datos actualizados correctamente")
    st.rerun()

# ==========================================
# SIDEBAR FILTROS
# ==========================================
with st.sidebar:

    st.markdown("## 🎛 Filtros")

    # PERIODO
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
# FECHAS ROBUSTAS (TIMESTAMP ISO)
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
# FUNCIÓN CON CACHE (5 MIN)
# ==========================================
@st.cache_data(ttl=300)
def obtener_datos(primer_dia, primer_dia_siguiente):
    todos = []
    limite = 1000
    inicio = 0

    while True:
        response = (
            supabase
            .table("kpi_ordenes_completadas")
            .select("*")
            .gte("fecha", primer_dia)
            .lt("fecha", primer_dia_siguiente)
            .range(inicio, inicio + limite - 1)
            .execute()
        )

        data = response.data

        if not data:
            break

        todos.extend(data)

        if len(data) < limite:
            break

        inicio += limite

    return todos


data = obtener_datos(primer_dia, primer_dia_siguiente)

if not data:
    st.warning("No hay datos para el período seleccionado.")
    st.stop()

df = pd.DataFrame(data)
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

# ==========================================
# FILTROS MULTISELECT (POWER BI STYLE)
# ==========================================
with st.sidebar:

    # CONTRATA
    opciones_contrata = sorted(df["contrata"].dropna().unique().tolist())
    contrata = st.multiselect(
        "Contrata",
        opciones_contrata,
        default=opciones_contrata
    )

    # TECNOLOGÍA
    opciones_tecnologia = sorted(df["tecnologia"].dropna().unique().tolist())
    tecnologia = st.multiselect(
        "Tecnología",
        opciones_tecnologia,
        default=opciones_tecnologia
    )

    # TIPO ACTIVIDAD
    opciones_tipo = sorted(df["tipo_actividad"].dropna().unique().tolist())
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
promedio_diario = round(total_ordenes / dias_operativos, 2) if dias_operativos > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Órdenes", f"{total_ordenes:,}")
col2.metric("Técnicos", total_tecnicos)
col3.metric("Días Operativos", dias_operativos)
col4.metric("Promedio Día", promedio_diario)

# ==========================================
# GRÁFICO
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

fig.update_layout(
    template="plotly_dark",
    height=280,
    margin=dict(l=10, r=10, t=10, b=10),
    coloraxis_showscale=False,
    xaxis_title="",
    yaxis_title=""
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# TABLAS
# ==========================================
col_tab1, col_tab2 = st.columns([1, 2])

with col_tab1:
    st.markdown("### 📍 Provincia")

    ordenes_provincia = (
        df.groupby("provincia")["orden_trabajo"]
        .nunique()
        .reset_index(name="Órdenes")
        .sort_values("Órdenes", ascending=False)
    )

    st.dataframe(ordenes_provincia, use_container_width=True, height=260)

with col_tab2:
    st.markdown("### 👷 Producción Técnico")

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

    st.dataframe(df_prod, use_container_width=True, height=260)
