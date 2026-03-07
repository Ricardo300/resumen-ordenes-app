import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(page_title="Dashboard Garantías", layout="wide")

st.title("Dashboard de Garantías")

# conexión supabase
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# función para traer datos
@st.cache_data
def cargar_garantias():

    response = (
        supabase
        .table("vista_garantias")
        .select("*")
        .execute()
    )

    df = pd.DataFrame(response.data)

    return df


df = cargar_garantias()

st.write("Total garantías:", len(df))

st.dataframe(df)
