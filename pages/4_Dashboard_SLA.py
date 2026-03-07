import streamlit as st
from supabase import create_client
import pandas as pd

# =====================================
# CONFIGURACIÓN
# =====================================

st.set_page_config(
    page_title="Dashboard SLA",
    layout="wide"
)

st.title("Dilación desde creación hasta cierre")

# =====================================
# CONEXIÓN SUPABASE
# =====================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =====================================
# CARGAR DATOS
# =====================================

response = supabase.table("view_sla_operacion").select("dilacion_dias,fecha").execute()

df = pd.DataFrame(response.data)

df["fecha"] = pd.to_datetime(df["fecha"])

# solo febrero
df = df[df["fecha"].dt.month == 2]

# =====================================
# CALCULO ACUMULADO
# =====================================

total = len(df)

tabla = []

for d in sorted(df["dilacion_dias"].unique()):

    dentro = len(df[df["dilacion_dias"] <= d])

    porcentaje = round((dentro / total) * 100,2)

    tabla.append({
        "Dilación": d,
        "Febrero %": porcentaje
    })

tabla_df = pd.DataFrame(tabla)

# =====================================
# MOSTRAR TABLA
# =====================================

st.dataframe(tabla_df, use_container_width=True)
