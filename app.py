import streamlit as st
from supabase import create_client
import pandas as pd

st.title("Base de datos ETA")

# Conexión
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# Consulta simple
response = supabase.table("eta_cruda").select("*").limit(200).execute()

# Convertir a DataFrame
df = pd.DataFrame(response.data)

# Mostrar
st.dataframe(df)
