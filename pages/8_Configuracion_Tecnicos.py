import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

st.set_page_config(
    page_title="Configuración Técnicos",
    layout="wide"
)

st.title("⚙️ Configuración de Técnicos")

if "mensaje_exito" not in st.session_state:
    st.session_state["mensaje_exito"] = None

if st.session_state["mensaje_exito"]:
    st.success(st.session_state["mensaje_exito"])
    st.session_state["mensaje_exito"] = None

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


@st.cache_data(ttl=300)
def cargar_tecnicos():
    response = (
        supabase
        .table("tabla_tecnicos_contrata")
        .select("*")
        .order("identificador_tecnico")
        .execute()
    )
    return response.data


def crear_tecnico(codigo, contrata, supervisor, backoffice, tecnologia):
    data = {
        "identificador_tecnico": codigo.strip().upper(),
        "contrata": contrata,
        "supervisor": supervisor,
        "backoffice_responsable": backoffice,
        "tecnologia": tecnologia,
        "estado_tecnico": "Activo",
        "fecha_alta": str(date.today()),
        "fecha_baja": None,
        "actualizado_por": "sistema"
    }

    supabase.table("tabla_tecnicos_contrata").insert(data).execute()


def actualizar_tecnico(fila):
    data = {
        "contrata": fila["contrata"],
        "supervisor": fila["supervisor"],
        "backoffice_responsable": fila["backoffice_responsable"],
        "tecnologia": fila["tecnologia"],
        "estado_tecnico": fila["estado_tecnico"],
        "actualizado_por": "sistema",
        "actualizado_en": "now()"
    }

    if fila["estado_tecnico"] == "Baja":
        data["fecha_baja"] = str(date.today())
    else:
        data["fecha_baja"] = None

    supabase.table("tabla_tecnicos_contrata").update(data).eq(
        "identificador_tecnico",
        fila["identificador_tecnico"]
    ).execute()


tecnicos = cargar_tecnicos()
df = pd.DataFrame(tecnicos)

if df.empty:
    st.warning("No hay técnicos cargados.")
    st.stop()

columnas_necesarias = [
    "identificador_tecnico",
    "contrata",
    "supervisor",
    "backoffice_responsable",
    "tecnologia",
    "estado_tecnico",
    "fecha_alta",
    "fecha_baja",
    "actualizado_por",
    "actualizado_en"
]

for col in columnas_necesarias:
    if col not in df.columns:
        df[col] = None

df["estado_tecnico"] = df["estado_tecnico"].fillna("Activo")

df_activos = df[df["estado_tecnico"] == "Activo"]

contratas = sorted(df["contrata"].dropna().unique().tolist())
supervisores = sorted(df["supervisor"].dropna().unique().tolist())
backoffices = sorted(df["backoffice_responsable"].dropna().unique().tolist())

st.subheader("📊 Resumen")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Activos", int((df["estado_tecnico"] == "Activo").sum()))
col2.metric("Baja", int((df["estado_tecnico"] == "Baja").sum()))
col3.metric("GPON", int((df_activos["tecnologia"] == "GPON").sum()))
col4.metric("DTH", int((df_activos["tecnologia"] == "DTH").sum()))
col5.metric("Sin supervisor", int(df_activos["supervisor"].isna().sum()))
col6.metric("Sin BO", int(df_activos["backoffice_responsable"].isna().sum()))

st.divider()

# ==========================================
# AGREGAR TÉCNICO NUEVO
# ==========================================
st.subheader("➕ Agregar nuevo técnico")

with st.form("form_nuevo_tecnico"):
    col_a, col_b, col_c, col_d, col_e = st.columns(
        [1.2, 1.5, 1.5, 1.5, 1]
    )

    with col_a:
        nuevo_codigo = st.text_input("Código técnico")

    with col_b:
        nueva_contrata = st.selectbox(
            "Contrata",
            ["Seleccione..."] + contratas
        )

    with col_c:
        nuevo_supervisor = st.selectbox(
            "Supervisor",
            ["Seleccione..."] + supervisores
        )

    with col_d:
        nuevo_backoffice = st.selectbox(
            "BackOffice",
            ["Seleccione..."] + backoffices
        )

    with col_e:
        nueva_tecnologia = st.selectbox(
            "Tecnología",
            ["Seleccione...", "GPON", "DTH"]
        )

    crear = st.form_submit_button(
        "Crear técnico",
        use_container_width=True
    )

    if crear:
        codigo_limpio = nuevo_codigo.strip().upper()

        if (
            not codigo_limpio
            or nueva_contrata == "Seleccione..."
            or nuevo_supervisor == "Seleccione..."
            or nuevo_backoffice == "Seleccione..."
            or nueva_tecnologia == "Seleccione..."
        ):
            st.warning("Debes completar todos los campos.")

        elif codigo_limpio in (
            df["identificador_tecnico"]
            .astype(str)
            .str.upper()
            .tolist()
        ):
            st.warning(f"El técnico {codigo_limpio} ya existe.")

        else:
            crear_tecnico(
                codigo_limpio,
                nueva_contrata,
                nuevo_supervisor,
                nuevo_backoffice,
                nueva_tecnologia
            )

            st.cache_data.clear()
            st.session_state["mensaje_exito"] = (
                f"Técnico {codigo_limpio} creado correctamente."
            )
            st.rerun()

st.divider()

# ==========================================
# FILTROS
# ==========================================
with st.sidebar:
    st.markdown("## 🎛 Filtros")

    filtro_estado = st.selectbox(
        "Estado",
        ["Todos"] + sorted(
            df["estado_tecnico"]
            .dropna()
            .unique()
            .tolist()
        )
    )

    filtro_contrata = st.selectbox(
        "Contrata",
        ["Todas"] + contratas
    )

    filtro_tecnologia = st.selectbox(
        "Tecnología",
        ["Todas"] + sorted(
            df["tecnologia"]
            .dropna()
            .unique()
            .tolist()
        )
    )

df_filtrado = df.copy()

if filtro_estado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["estado_tecnico"] == filtro_estado
    ]

if filtro_contrata != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["contrata"] == filtro_contrata
    ]

if filtro_tecnologia != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["tecnologia"] == filtro_tecnologia
    ]

st.subheader("📋 Técnicos registrados")

columnas_mostrar = [
    "identificador_tecnico",
    "contrata",
    "supervisor",
    "backoffice_responsable",
    "tecnologia",
    "estado_tecnico",
    "fecha_alta",
    "fecha_baja"
]

df_tabla = df_filtrado[columnas_mostrar].copy()

df_editado = st.data_editor(
    df_tabla,
    use_container_width=True,
    hide_index=True,
    disabled=[
        "identificador_tecnico",
        "fecha_alta",
        "fecha_baja"
    ],
    column_config={
        "contrata": st.column_config.SelectboxColumn(
            "Contrata",
            options=contratas
        ),
        "supervisor": st.column_config.SelectboxColumn(
            "Supervisor",
            options=supervisores
        ),
        "backoffice_responsable": st.column_config.SelectboxColumn(
            "BackOffice",
            options=backoffices
        ),
        "tecnologia": st.column_config.SelectboxColumn(
            "Tecnología",
            options=["GPON", "DTH"]
        ),
        "estado_tecnico": st.column_config.SelectboxColumn(
            "Estado",
            options=["Activo", "Baja"]
        )
    }
)

if st.button(
    "💾 Guardar cambios",
    type="primary"
):
    cambios = []

    df_original = df_tabla.set_index("identificador_tecnico")
    df_nuevo = df_editado.set_index("identificador_tecnico")

    columnas_editables = [
        "contrata",
        "supervisor",
        "backoffice_responsable",
        "tecnologia",
        "estado_tecnico"
    ]

    for codigo in df_nuevo.index:
        for columna in columnas_editables:
            valor_original = df_original.loc[codigo, columna]
            valor_nuevo = df_nuevo.loc[codigo, columna]

            if pd.isna(valor_original):
                valor_original = ""

            if pd.isna(valor_nuevo):
                valor_nuevo = ""

            if str(valor_original) != str(valor_nuevo):
                cambios.append(codigo)
                break

    cambios = list(set(cambios))

    if not cambios:
        st.warning("No se detectaron cambios.")
    else:
        for codigo in cambios:
            fila = df_nuevo.loc[codigo].to_dict()
            fila["identificador_tecnico"] = codigo
            actualizar_tecnico(fila)

        st.cache_data.clear()
        st.success(f"Se actualizaron {len(cambios)} técnico(s) correctamente.")
        st.rerun()