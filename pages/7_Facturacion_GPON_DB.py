import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(layout="wide")
st.title("Facturación GPON desde Supabase")

# 🔌 conexión
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# 🎯 filtro de fechas (simple por ahora)
fecha_inicio = st.date_input("Fecha inicio")
fecha_fin = st.date_input("Fecha fin")

if st.button("Cargar datos"):

    query = supabase.table("view_base_facturacion") \
        .select("*") \
        .gte("fecha", str(fecha_inicio)) \
        .lte("fecha", str(fecha_fin)) \
        .execute()

    data = query.data

    if len(data) == 0:
        st.warning("No hay datos en ese rango")
        st.stop()

    df = pd.DataFrame(data)

    st.subheader("Datos desde Supabase")
    st.dataframe(df.head(1500))
