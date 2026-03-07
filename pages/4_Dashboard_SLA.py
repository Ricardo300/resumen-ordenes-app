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
# CONSULTA SQL (solo febrero)
# =====================================

query = """
WITH base AS (

SELECT
dilacion_dias
FROM view_sla_operacion
WHERE DATE_TRUNC('month', fecha) = '2026-02-01'

)

SELECT
dilacion_dias,
ROUND(
SUM(COUNT(*)) OVER (ORDER BY dilacion_dias)::numeric
/
SUM(COUNT(*)) OVER () * 100
,2) AS febrero
FROM base
GROUP BY dilacion_dias
ORDER BY dilacion_dias
"""

response = supabase.rpc("run_sql", {"query": query}).execute()

df = pd.DataFrame(response.data)

# =====================================
# MOSTRAR TABLA
# =====================================

st.dataframe(
    df,
    use_container_width=True
)
