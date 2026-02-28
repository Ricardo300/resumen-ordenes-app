import streamlit as st
import pandas as pd

# ---------- CONFIG UI ----------
st.set_page_config(
    page_title="Dashboard de Órdenes",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Órdenes")

# ---------- CARGA ----------
archivo = st.file_uploader("📥 Sube el archivo Excel", type=["xlsx"])

if archivo is None:
    st.info("Sube un archivo .xlsx para ver el resumen.")
    st.stop()

df = pd.read_excel(archivo)

# Normalizamos nombres por si vienen con espacios
df.columns = [c.strip() for c in df.columns]

# Validación mínima
columnas_necesarias = ["Técnico", "Contrata"]
faltantes = [c for c in columnas_necesarias if c not in df.columns]
if faltantes:
    st.error(f"Tu Excel no trae estas columnas necesarias: {faltantes}")
    st.stop()

# ---------- SIDEBAR FILTROS ----------
st.sidebar.header("🎛️ Filtros")

# Contrata
contratas = sorted(df["Contrata"].dropna().astype(str).unique())
contrata_sel = st.sidebar.selectbox("Filtrar por Contrata", ["Todas"] + contratas)

df_filtrado = df.copy()
if contrata_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Contrata"].astype(str) == contrata_sel]

# (Opcional) filtro por tecnología si existe
if "Tecnología" in df_filtrado.columns:
    tecnologias = sorted(df_filtrado["Tecnología"].dropna().astype(str).unique())
    tec_sel = st.sidebar.multiselect("Filtrar por Tecnología", tecnologias, default=tecnologias)
    df_filtrado = df_filtrado[df_filtrado["Tecnología"].astype(str).isin(tec_sel)]

# ---------- KPIs (TARJETAS) ----------
total_ordenes = len(df_filtrado)
tecnicos_unicos = df_filtrado["Técnico"].nunique()
contratas_unicas = df_filtrado["Contrata"].nunique()

c1, c2, c3 = st.columns(3)
c1.metric("✅ Órdenes (filtradas)", f"{total_ordenes:,}")
c2.metric("👷 Técnicos", f"{tecnicos_unicos:,}")
c3.metric("🏢 Contratas", f"{contratas_unicas:,}")

st.divider()

# ---------- TABS ----------
tab1, tab2, tab3 = st.tabs(["👷 Por Técnico", "🏢 Por Contrata", "🧾 Datos (muestra)"])

# ---- TAB 1: Resumen por técnico
with tab1:
    st.subheader("Resumen por Técnico")

    resumen_tecnico = (
        df_filtrado["Técnico"]
        .astype(str)
        .value_counts()
        .reset_index()
    )
    resumen_tecnico.columns = ["Técnico", "Órdenes"]

    colA, colB = st.columns([2, 1])
    with colA:
        st.dataframe(resumen_tecnico, use_container_width=True)
    with colB:
        st.subheader("📌 Top 10 Técnicos")
        top10 = resumen_tecnico.head(10).set_index("Técnico")
        st.bar_chart(top10)

# ---- TAB 2: Resumen por contrata
with tab2:
    st.subheader("Resumen por Contrata")

    resumen_contrata = (
        df_filtrado["Contrata"]
        .astype(str)
        .value_counts()
        .reset_index()
    )
    resumen_contrata.columns = ["Contrata", "Órdenes"]

    colA, colB = st.columns([2, 1])
    with colA:
        st.dataframe(resumen_contrata, use_container_width=True)
    with colB:
        st.subheader("📌 Top Contratas")
        chart = resumen_contrata.set_index("Contrata")
        st.bar_chart(chart)

# ---- TAB 3: Datos
with tab3:
    st.subheader("Vista rápida del archivo (filtrado)")
    st.caption("Esto muestra una parte (no todo), para que sea ligero.")
    st.dataframe(df_filtrado.head(200), use_container_width=True)


