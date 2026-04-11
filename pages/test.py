import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(layout="wide")

st.title("Prueba Vista Garantías")

# conexión
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# consulta simple
response = supabase.table("vista_garantias").select("*").limit(100).execute()

data = response.data

# convertir a DataFrame
df = pd.DataFrame(data)

# mostrar
st.write("Columnas:", df.columns.tolist())
st.dataframe(df)
