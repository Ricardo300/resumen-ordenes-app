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
    # ==========================================
    # ADAPTAR DATAFRAME AL FORMATO DEL MOTOR
    # ==========================================
    df_motor = df.copy()
    
    df_motor["NUMERO DE ORDEN"] = df_motor["orden_trabajo"]
    df_motor["MATERIAL"] = df_motor["material"]
    df_motor["CANTIDAD"] = df_motor["cantidad"]
    df_motor["TIPO DE ORDEN"] = df_motor["sub_tipo_orden"]
    df_motor["TV"] = df_motor["cantidad_tv"]
    
    df_motor["CANTIDAD"] = pd.to_numeric(df_motor["CANTIDAD"], errors="coerce").fillna(0)
    df_motor["TV"] = pd.to_numeric(df_motor["TV"], errors="coerce").fillna(0)

    st.subheader("Vista previa formato motor")
    st.dataframe(df_motor[["NUMERO DE ORDEN", "MATERIAL", "CANTIDAD", "TIPO DE ORDEN", "TV"]].head(20))

    st.subheader("Datos desde Supabase")
    st.dataframe(df.head(1000))
