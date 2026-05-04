import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard Supervisión",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Dashboard Supervisión de Calidad")

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# ============================================================
# FUNCIONES
# ============================================================

def leer_hoja_excel(archivo, hoja):
    preview = pd.read_excel(archivo, sheet_name=hoja, header=None, nrows=15)

    fila_header = 0
    for i in range(len(preview)):
        valores = preview.iloc[i].astype(str).str.upper().str.strip().tolist()
        if "FECHA" in valores:
            fila_header = i
            break

    df = pd.read_excel(archivo, sheet_name=hoja, header=fila_header)
    df = df.dropna(how="all")
    df.columns = df.columns.astype(str).str.strip().str.upper()
    return df


def cargar_base_calidad(archivo):
    hojas = pd.ExcelFile(archivo).sheet_names

    configuracion = {
        "SUPERVISION GPON CLARO": ("GPON", "SUPERVISION"),
        "SUPERVISION DTH CLARO": ("DTH", "SUPERVISION"),
        "AUDITORIA GPON": ("GPON", "AUDITORIA"),
        "AUDITORIA DTH": ("DTH", "AUDITORIA"),
    }

    bases = []

    for nombre_base, (tecnologia, tipo_registro) in configuracion.items():
        hoja_real = next((h for h in hojas if h.strip().upper() == nombre_base), None)

        if hoja_real:
            df = leer_hoja_excel(archivo, hoja_real)
            df["TECNOLOGIA"] = tecnologia
            df["TIPO_REGISTRO"] = tipo_registro
            bases.append(df)

    if not bases:
        return pd.DataFrame()

    df_final = pd.concat(bases, ignore_index=True)

    if "FECHA" in df_final.columns:
        df_final["FECHA"] = pd.to_datetime(df_final["FECHA"], errors="coerce")
        df_final = df_final.dropna(subset=["FECHA"])
        df_final["AÑO"] = df_final["FECHA"].dt.year
        df_final["MES_NUM"] = df_final["FECHA"].dt.month
        df_final["MES"] = df_final["MES_NUM"].map(MESES_ES)
        df_final["DIA"] = df_final["FECHA"].dt.date
        df_final["SEMANA"] = df_final["FECHA"].dt.isocalendar().week.astype(int)

    return df_final


def filtro_checkbox(nombre, lista_valores, key, expanded=False):
    with st.sidebar.expander(nombre, expanded=expanded):
        col1, col2 = st.columns(2)

        if col1.button("✓ Todo", key=f"{key}_todo"):
            st.session_state[key] = lista_valores

        if col2.button("✕ Ninguno", key=f"{key}_ninguno"):
            st.session_state[key] = []

        estado_actual = st.session_state.get(key, lista_valores)

        seleccion = []
        for valor in lista_valores:
            marcado = st.checkbox(
                str(valor),
                value=valor in estado_actual,
                key=f"{key}_{valor}"
            )
            if marcado:
                seleccion.append(valor)

        st.session_state[key] = seleccion
        return seleccion

def calcular_positivos_negativos(df):
    columnas_excluir = [
        "FECHA", "AÑO", "MES", "MES_NUM", "DIA",
        "SUPERVISOR", "TECNICO", "TÉCNICO", "TECNICO AUDITADO",
        "ORDEN", "ORDEN AUDITADA", "EMPRESA", "CONTRATA",
        "TECNOLOGIA", "TIPO_REGISTRO",
        "REALIZA VISITA EN", "REALIZA VISITA EN:",

        "CLIENTE PERMITE ACCESO?",
        "ESTA BIEN TIPIFICADA",
        "PARAMETROS DE POTENCIA (POTENCIA-CALIDAD) SUPERIOR A 70",
        "CODIGO DE COMPLETAR CORRECTO",
        "REINCIDENCIA"
    ]

    columnas_evaluacion = [
        c for c in df.columns
        if c not in columnas_excluir
        and "OBSERV" not in c.upper()
        and "COMENT" not in c.upper()
        and "FOTO" not in c.upper()
        and "IMAGEN" not in c.upper()
        and "LINK" not in c.upper()
        and "URL" not in c.upper()
    ]

    positivos = 0
    negativos = 0

    for col in columnas_evaluacion:
        serie = df[col].astype(str).str.upper().str.strip()

        positivos += serie.isin(["VERDADERO", "TRUE", "SI", "SÍ", "CUMPLE", "1"]).sum()
        negativos += serie.isin(["FALSO", "FALSE", "NO", "NO CUMPLE", "0"]).sum()

    return positivos, negativos

# ============================================================
# CARGA DE ARCHIVO
# ============================================================

archivo = st.file_uploader(
    "📂 Cargar archivo Excel de supervisiones y auditorías",
    type=["xlsx"]
)

if archivo is None:
    st.info("Carga el archivo Excel para visualizar el dashboard.")
    st.stop()

df = cargar_base_calidad(archivo)

if df.empty:
    st.error("No se pudo cargar información válida del archivo.")
    st.stop()

# ============================================================
# FILTROS LATERALES
# ============================================================

st.sidebar.header("🔎 Filtros")

with st.sidebar.expander("📅 Periodo", expanded=True):
    años = sorted(df["AÑO"].dropna().unique(), reverse=True)
    filtro_anio = st.selectbox("Año", años)

    meses_df = (
        df[df["AÑO"] == filtro_anio][["MES_NUM", "MES"]]
        .drop_duplicates()
        .sort_values("MES_NUM")
    )

    filtro_mes = st.selectbox("Mes", meses_df["MES"].tolist())
    semanas_disponibles = ["Todas"] + sorted(
        df[
            (df["AÑO"] == filtro_anio) &
            (df["MES"] == filtro_mes)
        ]["SEMANA"].dropna().unique().tolist()
    )

    filtro_semana = st.selectbox("Semana calendario", semanas_disponibles)

tecnologias = sorted(df["TECNOLOGIA"].dropna().unique())
filtro_tecnologia = filtro_checkbox("🛰️ Tecnología", tecnologias, "filtro_tecnologia", True)

tipos = sorted(df["TIPO_REGISTRO"].dropna().unique())
filtro_tipo = filtro_checkbox("📊 Tipo de registro", tipos, "filtro_tipo", False)

if "SUPERVISOR" in df.columns:
    supervisores = sorted(df["SUPERVISOR"].dropna().unique())
    filtro_supervisor = filtro_checkbox("👷 Supervisor", supervisores, "filtro_supervisor", False)
else:
    filtro_supervisor = []

if "CONTRATA" in df.columns:
    contratas = sorted(df["CONTRATA"].dropna().unique())
    filtro_contrata = filtro_checkbox("🏢 Contrata", contratas, "filtro_contrata", False)
else:
    filtro_contrata = []

# ============================================================
# DATA FILTRADA
# ============================================================

df_filtrado = df[
    (df["AÑO"] == filtro_anio) &
    (df["MES"] == filtro_mes)
].copy()

if filtro_semana != "Todas":
    df_filtrado = df_filtrado[df_filtrado["SEMANA"] == filtro_semana]

if filtro_tecnologia:
    df_filtrado = df_filtrado[df_filtrado["TECNOLOGIA"].isin(filtro_tecnologia)]

if filtro_tipo:
    df_filtrado = df_filtrado[df_filtrado["TIPO_REGISTRO"].isin(filtro_tipo)]

if "SUPERVISOR" in df_filtrado.columns and filtro_supervisor:
    df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"].isin(filtro_supervisor)]

if "CONTRATA" in df_filtrado.columns and filtro_contrata:
    df_filtrado = df_filtrado[df_filtrado["CONTRATA"].isin(filtro_contrata)]

# ============================================================
# KPIS GENERALES
# ============================================================

total_supervisiones = len(df_filtrado[df_filtrado["TIPO_REGISTRO"] == "SUPERVISION"])
total_auditorias = len(df_filtrado[df_filtrado["TIPO_REGISTRO"] == "AUDITORIA"])

col_tecnico = "TECNICO AUDITADO" if "TECNICO AUDITADO" in df_filtrado.columns else None
tecnicos_revisados = df_filtrado[col_tecnico].nunique() if col_tecnico else 0

supervisores_activos = df_filtrado["SUPERVISOR"].nunique() if "SUPERVISOR" in df_filtrado.columns else 0

df_supervision_kpi = df_filtrado[df_filtrado["TIPO_REGISTRO"] == "SUPERVISION"]
positivos, negativos = calcular_positivos_negativos(df_supervision_kpi)
total_puntos = positivos + negativos
porcentaje_cumplimiento = positivos / total_puntos if total_puntos > 0 else 0

st.subheader("📌 Resumen general")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric("Supervisiones", f"{total_supervisiones:,}")
kpi2.metric("Auditorías", f"{total_auditorias:,}")
kpi3.metric("Técnicos revisados", f"{tecnicos_revisados:,}")
kpi4.metric("Puntos revisados", f"{total_puntos:,}")
kpi5.metric("% cumplimiento", f"{porcentaje_cumplimiento:.1%}")

st.divider()

# ============================================================
# GRÁFICO: SUPERVISIONES Y AUDITORÍAS POR DÍA
# ============================================================

st.subheader("📅 Supervisiones y auditorías por día")

df_dia = (
    df_filtrado
    .groupby(["DIA", "TIPO_REGISTRO"])
    .size()
    .reset_index(name="CANTIDAD")
)

if not df_dia.empty:

    fig_dia = px.bar(
        df_dia,
        x="DIA",
        y="CANTIDAD",
        color="TIPO_REGISTRO",
        text="CANTIDAD",
        barmode="group"
    )

    fig_dia.update_layout(
        height=420,
        xaxis_title="Día",
        yaxis_title="Cantidad",
        legend_title_text="Tipo",
        margin=dict(l=10, r=20, t=20, b=20)
    )

    fig_dia.update_traces(textposition="outside")

    st.plotly_chart(fig_dia, use_container_width=True)

else:
    st.info("No hay datos para mostrar por día.")

st.divider()

# ============================================================
# FILA 1 DE GRÁFICOS: SUPERVISIONES POR SUPERVISOR + VISITA EN
# ============================================================

import plotly.express as px

st.subheader("📊 Supervisiones de calidad")

df_supervision = df_filtrado[df_filtrado["TIPO_REGISTRO"] == "SUPERVISION"]

col_g1, col_g2 = st.columns([1.6, 1])

# ------------------------------------------------------------
# GRÁFICO 1: Supervisiones por supervisor
# ------------------------------------------------------------
with col_g1:
    st.markdown("### 👷 Supervisiones por supervisor")

    if not df_supervision.empty and "SUPERVISOR" in df_supervision.columns:

        resumen_supervisor = (
            df_supervision
            .groupby("SUPERVISOR")
            .size()
            .reset_index(name="CANTIDAD")
            .sort_values("CANTIDAD", ascending=True)
        )

        fig_supervisor = px.bar(
            resumen_supervisor,
            x="CANTIDAD",
            y="SUPERVISOR",
            orientation="h",
            text="CANTIDAD"
        )

        fig_supervisor.update_layout(
            height=420,
            xaxis_title="Cantidad de supervisiones",
            yaxis_title="Supervisor",
            showlegend=False,
            margin=dict(l=10, r=20, t=20, b=20)
        )

        fig_supervisor.update_traces(textposition="outside")

        st.plotly_chart(fig_supervisor, use_container_width=True)

    else:
        st.info("No hay datos de supervisión por supervisor para mostrar.")


# ------------------------------------------------------------
# GRÁFICO 2: Realiza la visita en
# ------------------------------------------------------------
with col_g2:
    
    st.markdown("### 📍 Realiza la visita en")
    columnas_disponibles = list(df_supervision.columns)

    columna_visita = next(
        (
            c for c in columnas_disponibles
            if "REALIZA" in c.upper()
            and "VISITA" in c.upper()
            and "EN" in c.upper()
        ),
        None
    )

    if not df_supervision.empty and columna_visita is not None:

        resumen_visita = (
            df_supervision[columna_visita]
            .dropna()
            .astype(str)
            .str.strip()
            .value_counts()
            .reset_index()
        )

        resumen_visita.columns = ["REALIZA VISITA EN", "CANTIDAD"]

        fig_visita = px.pie(
        resumen_visita,
        names="REALIZA VISITA EN",
        values="CANTIDAD",
        hole=0.45
        )

        fig_visita.update_traces(textinfo="percent+label")

        fig_visita.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.15,
        xanchor="center",
        x=0.5
    )
)

        st.plotly_chart(fig_visita, use_container_width=True)

    else:
        st.info("No se encontró columna de visita")
        st.write(columnas_disponibles)
# ============================================================
# FILA 2: PUNTOS EVALUADOS (POSITIVO VS NEGATIVO)
# ============================================================

st.divider()
st.subheader("🧪 Resultados por punto evaluado (Supervisión)")

df_supervision = df_filtrado[df_filtrado["TIPO_REGISTRO"] == "SUPERVISION"]

# Columnas a excluir
columnas_excluir = [
    "FECHA", "AÑO", "MES", "MES_NUM", "DIA",
    "SUPERVISOR", "TECNICO", "TÉCNICO", "TECNICO AUDITADO",
    "ORDEN", "ORDEN AUDITADA", "EMPRESA", "CONTRATA",
    "TECNOLOGIA", "TIPO_REGISTRO",
    "REALIZA VISITA EN", "REALIZA VISITA EN:",

    "CLIENTE PERMITE ACCESO?",
    "ESTA BIEN TIPIFICADA",
    "PARAMETROS DE POTENCIA (POTENCIA-CALIDAD) SUPERIOR A 70",
    "CODIGO DE COMPLETAR CORRECTO",
    "REINCIDENCIA"
]

columnas_puntos = [
    c for c in df_supervision.columns
    if c not in columnas_excluir
    and "OBSERV" not in c.upper()
    and "COMENT" not in c.upper()
    and "FOTO" not in c.upper()
    and "IMAGEN" not in c.upper()
    and "LINK" not in c.upper()
]

resultados = []

for col in columnas_puntos:
    serie = df_supervision[col].astype(str).str.upper().str.strip()

    positivos = serie.isin(["VERDADERO", "TRUE", "SI", "SÍ", "CUMPLE", "1"]).sum()
    negativos = serie.isin(["FALSO", "FALSE", "NO", "NO CUMPLE", "0"]).sum()

    total = positivos + negativos

    if total > 0:
        resultados.append({
            "PUNTO": col,
            "POSITIVO": positivos,
            "NEGATIVO": negativos
        })

df_puntos = pd.DataFrame(resultados)

if not df_puntos.empty:

    df_puntos = df_puntos.sort_values("POSITIVO", ascending=True)

    df_melt = df_puntos.melt(
        id_vars="PUNTO",
        value_vars=["POSITIVO", "NEGATIVO"],
        var_name="TIPO",
        value_name="CANTIDAD"
    )

    fig_puntos = px.bar(
        df_melt,
        x="CANTIDAD",
        y="PUNTO",
        color="TIPO",
        orientation="h",
        text="CANTIDAD",
        color_discrete_map={
            "POSITIVO": "#2ecc71",
            "NEGATIVO": "#e74c3c"
        }
    )

    fig_puntos.update_layout(
        barmode="stack",
        height=max(450, len(df_puntos) * 35),
        xaxis_title="Cantidad",
        yaxis_title="Punto evaluado",
        margin=dict(l=10, r=40, t=20, b=20)
    )

    fig_puntos.update_traces(textposition="inside")

    st.plotly_chart(fig_puntos, use_container_width=True)

else:
    st.info("No hay puntos evaluados disponibles.")
# ============================================================
# AUDITORÍAS GPON - PUNTOS EVALUADOS POR ETAPA
# ============================================================

st.divider()
st.subheader("🔍 Auditorías GPON - Puntos evaluados por etapa")

df_auditoria_gpon = df_filtrado[
    (df_filtrado["TIPO_REGISTRO"] == "AUDITORIA") &
    (df_filtrado["TECNOLOGIA"] == "GPON")
]

etapas_gpon = {
    "🟢 Etapa 1 - Uniforme y EPP": [
        "CAMISA", "PANTALON", "FAJA", "GUANTES", "ZAPATOS",
        "GAFETE", "CAPA", "CASCO", "ARNES COMPLETO"
    ],
    "🟡 Etapa 2 - Herramientas": [
        "ESCALERA 5 PELDAÑOS", "ESCALERA 28 PELDAÑOS",
        "CONOS DE SEGURIDAD", "PORTA CARRETES", "CAJA PARA HERRAMIENTAS",
        "ALICATE DE PUNTAS", "CORTADORA PARA CABLE", "ALICATE UNIVERSAL",
        "PONCHADORA PARA RJ-45", "PROBADOR DE CABLE UTP",
        "DESATORNILLADORES PHILIPS", "DESATORNILLADORES PLANOS",
        "JUEGO DE LLAVES COROFIJAS 10 A 14 MM", "JUEGO DE CUBOS",
        "ODOMETRO", "CINTA METRICA", "CUCHILLA", "MARTILLO",
        "PISTOLA DE SILICON", "EXTENSION ELECTRICA", "TALADRO",
        "BROCAS PASAMUROS 12 PULGADAS",
        "BROCAS PARA CONCRETO Y METAL 5/16\" Y 1/2\"",
        "GUIA DE FIBRA O NYLON DE 30 METROS",
        "SONDA METALICA 30 METROS",
        "ETIQUETADORA DYMO", "TIJERA PARA CORTAR KEVLAR",
        "PINZA PARA PELAR F.O",
        "KIT DE LIMPIEZA DE F.O (DEBE DE INCLUIR: TOALLAS LIBRES DE PELO, ALCOHOL ISOPROPILICO, LIMPIADOR DE CONECTORES SC)",
        "MEDIDOR DE POTENCIA OPTICO",
        "CORTADORA DE F.O CON ANGULO RECTO",
        "LAMPARA OPTICA DE 10MW",
        "TELEFONO ESTANDAR PARA VOIP",
        "INVERSOR", "MONITOR",
        "GANCHOS DE TIJERA PARA LEVANTAR TAPADERAS",
        "APARATO MOVIL COMPATIBLE CON WIFI 6"
    ],
    "🔵 Etapa 3 - Vehículo": [
        "PLACA", "MARCA", "AÑO", "LOGOS",
        "ESTADO DE CARROCERIA", "PORTA ESCALERA",
        "ESTADO DE NEUMATICOS", "ROTULADO DE UNIDAD",
        "PRESENTACION"
    ]
}


def acortar_texto(texto, limite=42):
    texto = str(texto)
    return texto if len(texto) <= limite else texto[:limite] + "..."


def grafico_auditoria_por_etapa(df_base, nombre_etapa, columnas_etapa):
    st.markdown(f"### {nombre_etapa}")

    resultados = []

    for col in columnas_etapa:
        if col not in df_base.columns:
            continue

        serie = df_base[col].astype(str).str.upper().str.strip()

        positivos = serie.isin(["VERDADERO", "TRUE", "SI", "SÍ", "CUMPLE", "1"]).sum()
        negativos = serie.isin(["FALSO", "FALSE", "NO", "NO CUMPLE", "0"]).sum()

        total = positivos + negativos

        if total > 0:
            resultados.append({
                "PUNTO_COMPLETO": col,
                "PUNTO": acortar_texto(col),
                "POSITIVO": positivos,
                "NEGATIVO": negativos
            })

    df_etapa = pd.DataFrame(resultados)

    if df_etapa.empty:
        st.info(f"No hay datos disponibles para {nombre_etapa}.")
        return

    df_etapa = df_etapa.sort_values("NEGATIVO", ascending=True)

    df_melt = df_etapa.melt(
        id_vars=["PUNTO", "PUNTO_COMPLETO"],
        value_vars=["POSITIVO", "NEGATIVO"],
        var_name="TIPO",
        value_name="CANTIDAD"
    )

    fig = px.bar(
        df_melt,
        x="CANTIDAD",
        y="PUNTO",
        color="TIPO",
        orientation="h",
        text="CANTIDAD",
        hover_data={"PUNTO_COMPLETO": True, "PUNTO": False},
        color_discrete_map={
            "POSITIVO": "#2ecc71",
            "NEGATIVO": "#e74c3c"
        }
    )

    fig.update_layout(
        barmode="stack",
        height=max(350, len(df_etapa) * 32),
        xaxis_title="Cantidad",
        yaxis_title="Punto evaluado",
        margin=dict(l=10, r=40, t=20, b=20),
        legend_title_text=""
    )

    fig.update_traces(textposition="inside")

    st.plotly_chart(fig, use_container_width=True)


if df_auditoria_gpon.empty:
    st.info("No hay datos de auditoría GPON disponibles.")
else:
    for nombre_etapa, columnas_etapa in etapas_gpon.items():
        grafico_auditoria_por_etapa(
            df_auditoria_gpon,
            nombre_etapa,
            columnas_etapa
        )
st.subheader("📋 Vista previa de datos filtrados")
st.dataframe(df_filtrado, use_container_width=True)