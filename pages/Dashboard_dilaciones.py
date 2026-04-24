import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(
    page_title="Dashboard Dilación por Fecha de Cierre",
    layout="wide"
)

st.markdown("""
<style>
[data-testid="stMetricValue"]{
    font-size:38px;
    font-weight:700;
}
[data-testid="stMetricLabel"]{
    font-size:15px;
}
.block-container{
    padding-top:2rem;
    max-width:1600px;
}
thead tr th {
    text-align: center !important;
}
tbody th {
    text-align: left !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
    <span style="font-size:30px;">📊</span>
    <h2 style="margin:0;font-weight:600;">
        DILACIÓN DE CIERRES POR DÍA
    </h2>
</div>
""", unsafe_allow_html=True)

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

@st.cache_data(ttl=300)
def cargar_datos():
    datos = []
    limite = 1000
    inicio = 0

    while True:
        response = (
            supabase
            .table("kpi_ordenes_completadas")
            .select("""
                orden_trabajo,
                fecha,
                hora_reserva_actividad,
                tecnologia,
                contrata,
                tipo_sla,
                provincia,
                municipio_canton
            """)
            .range(inicio, inicio + limite - 1)
            .execute()
        )

        data = response.data

        if not data:
            break

        datos.extend(data)
        inicio += limite

    return pd.DataFrame(datos)

df = cargar_datos()

if df.empty:
    st.warning("No se encontraron datos en kpi_ordenes_completadas.")
    st.stop()

# ==============================
# PREPARAR CAMPOS
# ==============================

df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.normalize()

df["hora_reserva_actividad"] = pd.to_datetime(
    df["hora_reserva_actividad"],
    errors="coerce"
)

df["fecha_creacion"] = df["hora_reserva_actividad"].dt.normalize()

for col in ["tecnologia", "contrata", "tipo_sla", "provincia", "municipio_canton"]:
    df[col] = df[col].astype(str).str.strip()
    df.loc[df[col].isin(["None", "nan", "NaT"]), col] = ""

df = df[
    df["fecha"].notna() &
    df["fecha_creacion"].notna()
].copy()

if df.empty:
    st.warning("No hay registros válidos con fecha de creación y fecha de cierre.")
    st.stop()

df["dilacion_dias"] = (df["fecha"] - df["fecha_creacion"]).dt.days

df = df[df["dilacion_dias"] >= 0].copy()

if df.empty:
    st.warning("No hay registros válidos después de calcular la dilación.")
    st.stop()

# Año y mes basados en fecha de cierre
df["anio"] = df["fecha"].dt.year
df["mes_num"] = df["fecha"].dt.month

meses_dict = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}

df["mes"] = df["mes_num"].map(meses_dict)

# ==============================
# FILTROS
# ==============================

st.sidebar.title("Filtros")

anios_disponibles = sorted(df["anio"].dropna().unique().tolist(), reverse=True)
anio = st.sidebar.selectbox("Año", anios_disponibles)

df_anio = df[df["anio"] == anio].copy()

meses_orden = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

meses_disponibles = [
    m for m in meses_orden
    if m in df_anio["mes"].dropna().unique().tolist()
]

mes = st.sidebar.selectbox("Mes", meses_disponibles)

df_mes = df_anio[df_anio["mes"] == mes].copy()

opciones_tec = ["Todas"] + sorted(
    [x for x in df_mes["tecnologia"].dropna().unique().tolist() if x != ""]
)

tec = st.sidebar.selectbox("Tecnología", opciones_tec)

df_f = df_mes.copy()

if tec != "Todas":
    df_f = df_f[df_f["tecnologia"] == tec]

opciones_contrata = ["Todas"] + sorted(
    [x for x in df_f["contrata"].dropna().unique().tolist() if x != ""]
)

contrata = st.sidebar.selectbox("Contrata", opciones_contrata)

if contrata != "Todas":
    df_f = df_f[df_f["contrata"] == contrata]

opciones_sla = ["Todos"] + sorted(
    [x for x in df_f["tipo_sla"].dropna().unique().tolist() if x != ""]
)

tipo_sla = st.sidebar.selectbox("Tipo SLA", opciones_sla)

if tipo_sla != "Todos":
    df_f = df_f[df_f["tipo_sla"] == tipo_sla]

opciones_provincia = ["Todas"] + sorted(
    [x for x in df_f["provincia"].dropna().unique().tolist() if x != ""]
)

provincia = st.sidebar.selectbox("Provincia", opciones_provincia)

if provincia != "Todas":
    df_f = df_f[df_f["provincia"] == provincia]

opciones_canton = ["Todos"] + sorted(
    [x for x in df_f["municipio_canton"].dropna().unique().tolist() if x != ""]
)

canton = st.sidebar.selectbox("Cantón", opciones_canton)

if canton != "Todos":
    df_f = df_f[df_f["municipio_canton"] == canton]

if df_f.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ==============================
# ELIMINAR DUPLICADOS
# ==============================

df_f = (
    df_f.sort_values(["fecha", "orden_trabajo"])
    .drop_duplicates(subset=["orden_trabajo"], keep="first")
    .copy()
)

# ==============================
# KPIs
# ==============================

total_ordenes = df_f["orden_trabajo"].nunique()

cerradas_dia_0 = (df_f["dilacion_dias"] == 0).sum()
cerradas_hasta_dia_1 = (df_f["dilacion_dias"] <= 1).sum()
cerradas_hasta_dia_2 = (df_f["dilacion_dias"] <= 2).sum()

pct_dia_0 = round((cerradas_dia_0 / total_ordenes) * 100, 2) if total_ordenes > 0 else 0
pct_dia_1 = round((cerradas_hasta_dia_1 / total_ordenes) * 100, 2) if total_ordenes > 0 else 0
pct_dia_2 = round((cerradas_hasta_dia_2 / total_ordenes) * 100, 2) if total_ordenes > 0 else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("📦 Total cerradas", total_ordenes)
col2.metric("⚡ Dilación día 0", f"{pct_dia_0}%")
col3.metric("📅 Acumulado hasta día 1", f"{pct_dia_1}%")
col4.metric("🛠 Acumulado hasta día 2", f"{pct_dia_2}%")

st.divider()

# ==============================
# TABLA MATRIZ POR FECHA
# ==============================

totales_por_fecha = (
    df_f.groupby("fecha")["orden_trabajo"]
    .nunique()
    .sort_index()
)

conteo = (
    df_f.groupby(["fecha", "dilacion_dias"])["orden_trabajo"]
    .nunique()
    .reset_index(name="cantidad")
)

pivot_exacto = conteo.pivot(
    index="dilacion_dias",
    columns="fecha",
    values="cantidad"
).fillna(0).sort_index()

max_dilacion = int(df_f["dilacion_dias"].max()) if not df_f.empty else 0

pivot_exacto = pivot_exacto.reindex(
    range(0, max_dilacion + 1),
    fill_value=0
)

pivot_acum = pivot_exacto.cumsum()

fechas_cols = list(pivot_exacto.columns)

matriz = {}

matriz["Total cerradas"] = {
    fecha: str(int(totales_por_fecha.get(fecha, 0)))
    for fecha in fechas_cols
}

for dia in pivot_exacto.index:
    fila = {}

    for fecha in fechas_cols:
        total = int(totales_por_fecha.get(fecha, 0))
        cantidad = int(pivot_exacto.loc[dia, fecha])
        acumulado = int(pivot_acum.loc[dia, fecha])

        if total == 0:
            fila[fecha] = ""
            continue

        if cantidad == 0:
            fila[fecha] = ""
            continue

        porcentaje_acum = (acumulado / total) * 100

        fila[fecha] = f"{cantidad} ({porcentaje_acum:.2f}%)"

    matriz[f"Día {dia}"] = fila

tabla_final = pd.DataFrame(matriz).T

columnas_formateadas = {
    col: pd.to_datetime(col).strftime("%d-%b")
    for col in tabla_final.columns
}

tabla_final = tabla_final.rename(columns=columnas_formateadas)

st.subheader("Matriz de dilación por fecha de cierre")
st.caption(
    "Cada columna representa las órdenes cerradas ese día. "
    "Cada celda muestra cantidad exacta por dilación y porcentaje acumulado por día."
)

st.dataframe(
    tabla_final,
    use_container_width=True,
    height=650
)

# ==============================
# TABLA RESUMEN GENERAL
# ==============================

st.divider()

total_por_dilacion = (
    df_f.groupby("dilacion_dias")["orden_trabajo"]
    .nunique()
    .reindex(range(0, max_dilacion + 1), fill_value=0)
)

total_acum = total_por_dilacion.cumsum()

resumen_general = []

resumen_general.append({
    "Dilación": "Total cerradas",
    "Cantidad": total_ordenes,
    "% Acumulado": "100.00%"
})

for dia in total_por_dilacion.index:
    cantidad = int(total_por_dilacion.loc[dia])

    if cantidad == 0:
        continue

    acumulado = int(total_acum.loc[dia])
    pct_acum = (acumulado / total_ordenes) * 100 if total_ordenes > 0 else 0

    resumen_general.append({
        "Dilación": f"Día {dia}",
        "Cantidad": cantidad,
        "% Acumulado": f"{pct_acum:.2f}%"
    })

resumen_general_df = pd.DataFrame(resumen_general)

st.subheader("Resumen general del período")
st.caption(
    "Este resumen consolida todos los días filtrados. "
    "La cantidad es exacta por dilación y el porcentaje es acumulado sobre el total cerrado."
)

st.dataframe(
    resumen_general_df,
    use_container_width=True,
    hide_index=True
)
