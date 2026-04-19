import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Órdenes Factibles", layout="wide")

st.title("Dashboard de Órdenes Factibles")

# =========================
# CARGA DE ARCHIVO
# =========================
archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo, sheet_name="Hoja1")

    # -------------------------
    # LIMPIEZA BÁSICA
    # -------------------------
    df.columns = df.columns.str.strip()

    # Normalizar ANALISIS
    if "ANALISIS" not in df.columns:
        st.error("No se encontró la columna 'ANALISIS' en el archivo.")
        st.stop()

    df["ANALISIS"] = df["ANALISIS"].astype(str).str.strip()

    # Crear clasificación principal
    df["Factibilidad"] = df["ANALISIS"].apply(
        lambda x: "Factible" if x.upper() == "COMPLETADO" else "No Factible"
    )

    # =========================
    # FILTRO OPCIONAL
    # =========================
    with st.sidebar:
        st.header("Filtros")

        lista_analisis = sorted(df["ANALISIS"].dropna().unique().tolist())
        seleccion_analisis = st.multiselect(
            "ANALISIS",
            options=lista_analisis,
            default=lista_analisis
        )

    df_filtrado = df[df["ANALISIS"].isin(seleccion_analisis)].copy()

    # =========================
    # MÉTRICAS
    # =========================
    total_ordenes = len(df_filtrado)
    factibles = (df_filtrado["Factibilidad"] == "Factible").sum()
    no_factibles = (df_filtrado["Factibilidad"] == "No Factible").sum()

    pct_factibles = (factibles / total_ordenes * 100) if total_ordenes > 0 else 0
    pct_no_factibles = (no_factibles / total_ordenes * 100) if total_ordenes > 0 else 0

    # =========================
    # FILA 1 - KPIs
    # =========================
    st.subheader("Resumen General")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Total Órdenes", f"{total_ordenes:,}")
    c2.metric("Factibles", f"{factibles:,}")
    c3.metric("No Factibles", f"{no_factibles:,}")
    c4.metric("% Factibilidad", f"{pct_factibles:.1f}%")
    c5.metric("% No Factibilidad", f"{pct_no_factibles:.1f}%")

    # =========================
    # FILA 2
    # =========================
    col1, col2 = st.columns((1, 1.4))

    # -------------------------
    # GRAFICO 1: DONA FACTIBLE / NO FACTIBLE
    # -------------------------
    resumen_factibilidad = (
        df_filtrado["Factibilidad"]
        .value_counts()
        .rename_axis("Factibilidad")
        .reset_index(name="Cantidad")
    )

    with col1:
        st.subheader("Factible vs No Factible")

        fig_dona = px.pie(
            resumen_factibilidad,
            names="Factibilidad",
            values="Cantidad",
            hole=0.55
        )

        fig_dona.update_traces(
            textposition="inside",
            textinfo="percent+label"
        )

        fig_dona.update_layout(
            margin=dict(l=10, r=10, t=40, b=10),
            legend_title_text=""
        )

        st.plotly_chart(fig_dona, use_container_width=True)

    # -------------------------
    # GRAFICO 2: NO FACTIBLES POR ANALISIS
    # -------------------------
    no_fact_df = df_filtrado[df_filtrado["Factibilidad"] == "No Factible"].copy()

    resumen_no_fact = (
        no_fact_df["ANALISIS"]
        .value_counts()
        .reset_index()
    )
    resumen_no_fact.columns = ["ANALISIS", "Cantidad"]

    with col2:
        st.subheader("No Factibles por ANALISIS")

        fig_bar = px.bar(
            resumen_no_fact,
            x="Cantidad",
            y="ANALISIS",
            orientation="h",
            text="Cantidad"
        )

        fig_bar.update_traces(textposition="outside")

        fig_bar.update_layout(
            yaxis=dict(categoryorder="total ascending"),
            margin=dict(l=10, r=30, t=40, b=10),
            xaxis_title="Cantidad",
            yaxis_title=""
        )

        st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("Sube el archivo Excel para mostrar el dashboard.")
