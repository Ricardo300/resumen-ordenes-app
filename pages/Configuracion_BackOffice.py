import streamlit as st
import pandas as pd
from supabase import create_client

# =========================================
# CONFIGURACIÓN SUPABASE
# =========================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================================
# LISTA FIJA BACKOFFICE
# =========================================

BACKOFFICE_PERSONAS = [
    "Sin asignar",
    "Adriana Rojas",
    "Sofía Álvarez",
    "Andres Corea",
    "Harold Castillo",
    "Luiggi Dalolio",
    "Cristina Díaz",
]

# =========================================
# TÍTULO
# =========================================

st.title("⚙️ Configuración BackOffice Responsable")

st.caption("Asignación de BackOffice por contrata")

# =========================================
# CARGAR DATOS
# =========================================

response = (
    supabase
    .table("tabla_tecnicos_contrata")
    .select("contrata, backoffice_responsable")
    .execute()
)

df = pd.DataFrame(response.data)

if df.empty:
    st.warning("No hay datos.")
    st.stop()

# =========================================
# LIMPIEZA
# =========================================

df["contrata"] = df["contrata"].fillna("SIN CONTRATA")

df["backoffice_responsable"] = (
    df["backoffice_responsable"]
    .fillna("Sin asignar")
)

df_config = (
    df.groupby("contrata", as_index=False)
    .agg({"backoffice_responsable": "first"})
    .sort_values("contrata")
)

# =========================================
# FORMULARIO
# =========================================

st.subheader("📋 Asignar BackOffice por Contrata")

cambios = {}

with st.form("form_backoffice"):

    for _, row in df_config.iterrows():

        contrata = row["contrata"]
        responsable_actual = row["backoffice_responsable"]

        if responsable_actual not in BACKOFFICE_PERSONAS:
            responsable_actual = "Sin asignar"

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(
                f"""
                <div style="
                    padding-top:10px;
                    font-weight:700;
                    font-size:15px;
                ">
                    {contrata}
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            nuevo_responsable = st.selectbox(
                label=f"bo_{contrata}",
                options=BACKOFFICE_PERSONAS,
                index=BACKOFFICE_PERSONAS.index(responsable_actual),
                key=f"bo_{contrata}",
                label_visibility="collapsed"
            )

        cambios[contrata] = nuevo_responsable

    guardar = st.form_submit_button("💾 Guardar configuración")

# =========================================
# GUARDAR
# =========================================

if guardar:

    total = 0

    for contrata, responsable in cambios.items():

        responsable_guardar = (
            None if responsable == "Sin asignar"
            else responsable
        )

        (
            supabase
            .table("tabla_tecnicos_contrata")
            .update({
                "backoffice_responsable": responsable_guardar
            })
            .eq("contrata", contrata)
            .execute()
        )

        total += 1

    st.success(f"Configuración guardada correctamente ({total} contratas)")
    st.rerun()

# =========================================
# TABLA ACTUAL
# =========================================

st.subheader("Configuración actual")

st.dataframe(
    df_config,
    use_container_width=True,
    hide_index=True
)