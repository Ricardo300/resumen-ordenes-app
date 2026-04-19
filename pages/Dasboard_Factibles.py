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
    df.columns = df.columns.str.strip()

    # =========================
    # VALIDAR COLUMNAS NECESARIAS
    # =========================
    columnas_requeridas = ["Factibilidad", "Clasificación General"]
    faltantes = [col for col in columnas_requeridas if col not in df.columns]

    if faltantes:
        st.error(f"Faltan estas columnas en el archivo: {', '.join(faltantes)}")
        st.stop()

    # =========================
    # LIMPIEZA BÁSICA
    # =========================
    df["Factibilidad"] = df["Factibilidad"].astype(str).str.strip()
    df["Clasificación General"] = df["Clasificación General"].astype(str).str.strip()

    # Buscar columna de tecnología
    col_tecnologia = None
    for col in df.columns:
        if col.strip().lower() == "tecnología" or col.strip().lower() == "tecnologia":
            col_tecnologia = col
            break

    if col_tecnologia is None:
        st.warning("No se encontró la columna de Tecnología. El filtro no se mostrará.")
        df["Tecnología_tmp"] = "SIN DATO"
        col_tecnologia = "Tecnología_tmp"

    df[col_tecnologia] = df[col_tecnologia].astype(str).str.strip()

    # Buscar columna de fecha para días operativos
    posibles_fechas = ["Fecha Atención", "Fecha", "fecha", "FECHA ATENCION"]
    col_fecha = None
    for col in posibles_fechas:
        if col in df.columns:
            col_fecha = col
            break

    if col_fecha is not None:
        df[col_fecha] = pd.to_datetime(df[col_fecha], errors="coerce")
    else:
        st.warning("No se encontró columna de fecha para calcular días operativos.")

    # =========================
    # FILTROS
    # =========================
    with st.sidebar:
        st.header("Filtros")

        tecnologias = sorted(df[col_tecnologia].dropna().unique().tolist())
        tecnologia_sel = st.multiselect(
            "Tecnología",
            options=tecnologias,
            default=tecnologias
        )

    df_filtrado = df[df[col_tecnologia].isin(tecnologia_sel)].copy()

    # =========================
    # KPIs
    # =========================
    total_ordenes = len(df_filtrado)

    factibles = df_filtrado["Factibilidad"].str.upper().eq("FACTIBLE").sum()
    no_factibles = df_filtrado["Factibilidad"].str.upper().eq("NO FACTIBLE").sum()

    pct_factibles = (factibles / total_ordenes * 100) if total_ordenes > 0 else 0
    pct_no_factibles = (no_factibles / total_ordenes * 100) if total_ordenes > 0 else 0

    if col_fecha is not None:
        dias_operativos = df_filtrado[col_fecha].dropna().dt.date.nunique()
    else:
        dias_operativos = 0

    # =========================
    # FILA 1 - KPIs
    # =========================
    st.subheader("Resumen General")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("Total Órdenes", f"{total_ordenes:,}")
    c2.metric("Factibles", f"{factibles:,}")
    c3.metric("No Factibles", f"{no_factibles:,}")
    c4.metric("% Factibilidad", f"{pct_factibles:.1f}%")
    c5.metric("% No Factibilidad", f"{pct_no_factibles:.1f}%")
    c6.metric("Días Operativos", f"{dias_operativos:,}")

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
    # GRAFICO 2: NO FACTIBLES POR CLASIFICACIÓN GENERAL
    # -------------------------
    no_fact_df = df_filtrado[
        df_filtrado["Factibilidad"].str.upper() == "NO FACTIBLE"
    ].copy()

    resumen_clasif = (
        no_fact_df["Clasificación General"]
        .fillna("SIN CLASIFICAR")
        .replace("", "SIN CLASIFICAR")
        .value_counts()
        .reset_index()
    )
    resumen_clasif.columns = ["Clasificación General", "Cantidad"]

    with col2:
        st.subheader("No Factibles por Clasificación General")

        fig_bar = px.bar(
            resumen_clasif,
            x="Cantidad",
            y="Clasificación General",
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
