import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
from datetime import datetime
from calendar import monthrange

# ==========================================
# LOGIN SIMPLE
# ==========================================

usuarios = {
    "ricardo": "1234",
    "jeffrey": "12345",
    "hector": "123456",
    "supervisor": "abcd",
    "backoffice": "eta2026"
}

if "logueado" not in st.session_state:
    st.session_state["logueado"] = False


def login():
    st.title("🔐 Acceso al Dashboard")

    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if usuario in usuarios and usuarios[usuario] == contraseña:
            st.session_state["logueado"] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")


if not st.session_state["logueado"]:
    login()
    st.stop()

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
# FILTRO FECHA ESTILO POWER BI
# ==========================================

primer_dia_mes = datetime(año, mes, 1)
ultimo_dia_mes = datetime(año, mes, monthrange(año, mes)[1])

with st.sidebar.expander("Fecha", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        fecha_inicio = st.date_input("Inicio", value=primer_dia_mes)

    with col2:
        fecha_fin = st.date_input("Fin", value=ultimo_dia_mes)

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
            .order("fecha", desc=False)
            .order("orden_trabajo", desc=False)
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

# ==========================================
# LIMPIEZA BASE
# ==========================================
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

for col in ["orden_trabajo", "contrata", "tecnologia", "tipo_actividad", "identificador_tecnico", "garantia", "provincia", "tipo_sla"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# ==========================================
# FILTRO CHECKBOX + BOTONES TODO/NINGUNO
# ==========================================
def filtro_checkbox(label, opciones, key_prefix):
    with st.sidebar.expander(label, expanded=False):
        col1, col2 = st.columns(2)

        if col1.button("✓ Todo", key=f"{key_prefix}_all", type="secondary"):
            for opcion in opciones:
                st.session_state[f"{key_prefix}_{opcion}"] = True

        if col2.button("✕ Ninguno", key=f"{key_prefix}_none", type="secondary"):
            for opcion in opciones:
                st.session_state[f"{key_prefix}_{opcion}"] = False

        seleccionados = []

        for opcion in opciones:
            estado_key = f"{key_prefix}_{opcion}"
            if estado_key not in st.session_state:
                st.session_state[estado_key] = True

            estado = st.checkbox(opcion, key=estado_key)
            if estado:
                seleccionados.append(opcion)

    return seleccionados

# Opciones dinámicas
opciones_contrata = sorted(df["contrata"].dropna().unique().tolist())
opciones_tecnologia = sorted(df["tecnologia"].dropna().unique().tolist())
opciones_tipo = sorted(df["tipo_actividad"].dropna().unique().tolist())
opciones_tipo_sla = sorted(df["tipo_sla"].dropna().unique().tolist())

contrata = filtro_checkbox("Contrata", opciones_contrata, "con")
tecnologia = filtro_checkbox("Tecnología", opciones_tecnologia, "tec")
tipo_actividad = filtro_checkbox("Tipo Actividad", opciones_tipo, "tip")
tipo_sla = filtro_checkbox("Tipo SLA", opciones_tipo_sla, "sla")

# ==========================================
# APLICAR FILTROS
# ==========================================
df = df[
    df["tecnologia"].isin(tecnologia) &
    df["contrata"].isin(contrata) &
    df["tipo_actividad"].isin(tipo_actividad) &
    df["tipo_sla"].isin(tipo_sla)
]

df = df[
    (df["fecha"].dt.date >= fecha_inicio) &
    (df["fecha"].dt.date <= fecha_fin)
].copy()

# ==========================================
# DESDUPLICACIÓN DEFENSIVA
# ==========================================
registros_filtrados = len(df)

# Si por cambios en el orden físico / paginación entró una misma orden más de una vez,
# nos quedamos con la primera aparición estable.
df = (
    df.sort_values(["fecha", "orden_trabajo"], ascending=[True, True])
      .drop_duplicates(subset=["orden_trabajo"], keep="first")
      .reset_index(drop=True)
)

ordenes_unicas_final = len(df)

# resetear popup cuando cambian filtros
st.session_state["dia_click"] = None

if df.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ==========================================
# MÉTRICAS
# ==========================================
total_ordenes = df["orden_trabajo"].nunique()
total_tecnicos = df["identificador_tecnico"].nunique()
dias_operativos = df["fecha"].dt.date.nunique()
promedio_diario = round(total_ordenes / dias_operativos, 2) if dias_operativos else 0
total_garantias = len(df[df["garantia"].astype(str).str.strip().str.upper() == "SI"])

# ------------------------------------------
# PRODUCTIVIDAD POR TÉCNICO
# ------------------------------------------
productividad_tecnico = (
    df.groupby("identificador_tecnico")
    .agg(
        produccion=("orden_trabajo", "nunique"),
        dias_trabajados=("fecha", lambda x: x.dt.date.nunique())
    )
    .reset_index()
)

productividad_tecnico["productividad"] = (
    productividad_tecnico["produccion"] / productividad_tecnico["dias_trabajados"]
)

# KPI principal: promedio por técnico
productividad_promedio = round(
    productividad_tecnico["productividad"].mean(), 2
) if not productividad_tecnico.empty else 0

# KPI nuevo: mediana por técnico
productividad_mediana = round(
    productividad_tecnico["productividad"].median(), 2
) if not productividad_tecnico.empty else 0

# ------------------------------------------
# KPIs
# ------------------------------------------
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
c1.metric("Órdenes", f"{total_ordenes:,}")
c2.metric("Técnicos", total_tecnicos)
c3.metric("Prod. Promedio", productividad_promedio)
c4.metric("Prod. Mediana", productividad_mediana)
c5.metric("Días Operativos", dias_operativos)
c6.metric("Promedio Día", promedio_diario)
c7.metric("Garantías", total_garantias)
# ==========================================
# POPUP TÉCNICOS
# ==========================================
@st.dialog("Técnicos del día")
def mostrar_tecnicos(dia):
    lista_tecnicos = (
        df[df["dia_mes"] == dia]
        .groupby("identificador_tecnico")["orden_trabajo"]
        .nunique()
        .reset_index(name="ordenes_atendidas")
        .sort_values("ordenes_atendidas", ascending=False)
    )

    st.write(f"Técnicos que trabajaron el día {dia}")
    st.dataframe(lista_tecnicos, use_container_width=True)

    st.download_button(
        "Descargar lista",
        lista_tecnicos.to_csv(index=False),
        file_name=f"tecnicos_dia_{dia}.csv",
        mime="text/csv"
    )

# ==========================================
# GRÁFICO ÓRDENES POR DÍA + TÉCNICOS
# ==========================================
df["dia_mes"] = df["fecha"].dt.day

ordenes_dia = (
    df.groupby("dia_mes")["orden_trabajo"]
    .nunique()
    .reset_index(name="ordenes")
)

tecnicos_dia = (
    df.groupby("dia_mes")["identificador_tecnico"]
    .nunique()
    .reset_index(name="tecnicos")
)

ordenes_dia = ordenes_dia.merge(tecnicos_dia, on="dia_mes")

fig = px.bar(
    ordenes_dia,
    x="dia_mes",
    y="ordenes",
    text="ordenes",
    color="ordenes",
    color_continuous_scale="Blues"
)

fig.update_traces(textposition="outside", opacity=0.65)

fig.add_scatter(
    x=ordenes_dia["dia_mes"],
    y=ordenes_dia["tecnicos"],
    mode="lines+markers+text",
    text=ordenes_dia["tecnicos"],
    textposition="top center",
    line=dict(color="#FF3B30", width=1.5),
    marker=dict(size=5),
    name="Técnicos"
)

fig.update_layout(
    height=350,
    template="plotly_dark",
    xaxis_title="Día del mes",
    yaxis_title="Órdenes Completas",
    coloraxis_showscale=False
)

st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    key="grafico_ordenes_dia"
)

# ==========================================
# GUARDAR DÍA SELECCIONADO
# ==========================================
if "dia_click" not in st.session_state:
    st.session_state["dia_click"] = None

event = st.session_state.get("grafico_ordenes_dia")

if event and "selection" in event and event["selection"]["points"]:
    st.session_state["dia_click"] = event["selection"]["points"][0]["x"]

# ==========================================
# MOSTRAR TÉCNICOS
# ==========================================
if st.session_state["dia_click"]:
    mostrar_tecnicos(st.session_state["dia_click"])

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
            Producción=("orden_trabajo", "nunique"),
            Dias_Trabajados=("fecha", "nunique")
        )
        .reset_index()
    )
    df_prod["Productividad"] = (df_prod["Producción"] / df_prod["Dias_Trabajados"]).round(2)
    df_prod = df_prod.drop(columns=["Dias_Trabajados"]).sort_values("Producción", ascending=False)
    st.dataframe(df_prod, use_container_width=True, height=300)

# ==========================================
# GRÁFICO CUMPLIMIENTO META 4 ÓRDENES
# ==========================================
st.subheader("Promedio de Órdenes por Técnico por Contrata")

ordenes_tecnico = (
    df.groupby(["fecha", "contrata", "identificador_tecnico"])["orden_trabajo"]
      .nunique()
      .reset_index(name="ordenes")
)

promedio_contrata = (
    ordenes_tecnico.groupby("contrata")["ordenes"]
      .mean()
      .reset_index()
      .sort_values("ordenes", ascending=False)
)

fig = px.bar(
    promedio_contrata,
    x="contrata",
    y="ordenes",
    text_auto=".2f"
)

colors = ["#1565C0" if i % 2 == 0 else "#90CAF9" for i in range(len(promedio_contrata))]
fig.update_traces(marker_color=colors, width=0.6)
fig.update_layout(bargap=0.15)

fig.add_hline(
    y=4,
    line_dash="dash",
    line_color="red",
    annotation_text="Meta 4 órdenes",
    annotation_position="top right"
)

fig.update_layout(
    showlegend=False,
    xaxis_title="Contrata",
    yaxis_title="Órdenes promedio",
    xaxis_tickangle=-90,
    template="plotly_dark",
    margin=dict(b=120)
)

st.plotly_chart(
    fig,
    use_container_width=True,
    key="grafico_productividad_contrata"
)

# ==========================================
# GRÁFICO CUMPLIMIENTO POR TÉCNICO
# ==========================================
fecha_seleccionada = st.date_input(
    "Seleccionar día",
    value=df["fecha"].dropna().min().date()
)

df_dia = df[df["fecha"].dt.date == fecha_seleccionada]

ordenes_tecnico_dia = (
    df_dia.groupby("identificador_tecnico")["orden_trabajo"]
    .nunique()
    .reset_index(name="ordenes")
)

if ordenes_tecnico_dia.empty:
    st.info("No hay órdenes completadas para el día seleccionado.")
else:
    ordenes_tecnico_dia = ordenes_tecnico_dia.sort_values("ordenes", ascending=False)
    ordenes_tecnico_dia["indice"] = range(len(ordenes_tecnico_dia))

    fig_tecnico = px.bar(
        ordenes_tecnico_dia,
        x="indice",
        y="ordenes",
        text_auto=True
    )

    fig_tecnico.update_xaxes(
        tickmode="array",
        tickvals=ordenes_tecnico_dia["indice"],
        ticktext=ordenes_tecnico_dia["identificador_tecnico"],
        tickangle=-90,
        range=[0, 19]
    )

    colors = ["#0D47A1" if i % 2 == 0 else "#90CAF9" for i in range(len(ordenes_tecnico_dia))]
    fig_tecnico.update_traces(marker_color=colors, width=0.6)

    fig_tecnico.add_hline(
        y=4,
        line_dash="dash",
        line_color="red",
        annotation_text="Meta 4 órdenes",
        annotation_position="top right"
    )

    fig_tecnico.update_layout(
        template="plotly_dark",
        height=600,
        xaxis_title="Técnico",
        yaxis_title="Órdenes atendidas",
        bargap=0.15
    )

    st.plotly_chart(fig_tecnico, use_container_width=True, key="grafico_tecnicos_por_dia")
