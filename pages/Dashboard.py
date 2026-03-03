import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(layout="wide")
st.title("📊 Dashboard KPI ETA")

# ==========================================
# ACTUALIZAR CACHE
# ==========================================
if st.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("## 🎛 Filtros")

    año = st.selectbox("Año", [2026, 2025, 2024], index=0)

    meses_dict = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
        "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
        "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
    }

    mes_nombre = st.selectbox("Mes", list(meses_dict.keys()))
    mes = meses_dict[mes_nombre]

# ==========================================
# FECHAS ISO
# ==========================================
primer_dia = f"{año}-{mes:02d}-01T00:00:00"

if mes == 12:
    siguiente_mes = 1
    siguiente_año = año + 1
else:
    siguiente_mes = mes + 1
    siguiente_año = año

primer_dia_siguiente = f"{siguiente_año}-{siguiente_mes:02d}-01T00:00:00"

# ==========================================
# CONEXIÓN SUPABASE
# ==========================================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

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
df["fecha"] = pd.to_datetime(df["fecha"])

# ==========================================
# FUNCIÓN MULTISELECT CHECKBOX
# ==========================================
def filtro_checkbox(label, opciones, key_prefix):

    seleccionados = []

    with st.sidebar.expander(label, expanded=False):
        for opcion in opciones:
            estado = st.checkbox(
                opcion,
                value=True,
                key=f"{key_prefix}_{opcion}"
            )
            if estado:
                seleccionados.append(opcion)

    return seleccionados


# ==========================================
# FILTROS
# ==========================================
opciones_tecnologia = sorted(df["tecnologia"].dropna().unique())
opciones_contrata = sorted(df["contrata"].dropna().unique())
opciones_tipo = sorted(df["tipo_actividad"].dropna().unique())

tecnologia = filtro_checkbox("Tecnología", opciones_tecnologia, "tec")
contrata = filtro_checkbox("Contrata", opciones_contrata, "con")
tipo_actividad = filtro_checkbox("Tipo Actividad", opciones_tipo, "tip")

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

c1.metric("Órdenes", total_ordenes)
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

st.markdown("## 📋 Detalle Operativo")

col_tab1, col_tab2 = st.columns([1, 2])

# -----------------------------
# TABLA POR PROVINCIA
# -----------------------------
with col_tab1:
    st.markdown("### 📍 Órdenes por Provincia")

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

# -----------------------------
# TABLA PRODUCTIVIDAD
# -----------------------------
with col_tab2:
    st.markdown("### 👷 Producción y Productividad por Técnico")

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
