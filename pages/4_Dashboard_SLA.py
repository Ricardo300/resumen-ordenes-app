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
# CARGAR DATOS (PAGINACIÓN)
# =====================================

datos = []
limite = 1000
inicio = 0

while True:

    response = (
        supabase
        .table("view_sla_operacion")
        .select("dilacion_dias,fecha")
        .range(inicio, inicio + limite - 1)
        .execute()
    )

    data = response.data

    if not data:
        break

    datos.extend(data)
    inicio += limite

df = pd.DataFrame(datos)

# =====================================
# FILTRO FEBRERO 2026
# =====================================

df["fecha"] = pd.to_datetime(df["fecha"])

df = df[
    (df["fecha"].dt.year == 2026) &
    (df["fecha"].dt.month == 2)
]

# =====================================
# CALCULAR TABLA
# =====================================

conteo = (
    df.groupby("dilacion_dias")
    .size()
    .reset_index(name="Cantidad")
    .sort_values("dilacion_dias")
)

total = conteo["Cantidad"].sum()

conteo["Acumulado"] = conteo["Cantidad"].cumsum()

conteo["Febrero %"] = round((conteo["Acumulado"] / total) * 100, 2)

tabla_df = conteo.rename(columns={"dilacion_dias": "Dilación"})[
    ["Dilación", "Cantidad", "Febrero %"]
]

# =====================================
# MOSTRAR TABLA
# =====================================

st.dataframe(
    tabla_df,
    use_container_width=True,
    hide_index=True
)
