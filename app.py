import streamlit as st
from supabase import create_client
import pandas as pd

st.title("Base de datos ETA")

# Conexión Supabase
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ===============================
# 1️⃣ MOSTRAR BASE COMPLETA
# ===============================

st.subheader("Datos actuales en base")

all_data = []
offset = 0
limit = 1000

while True:
    response = supabase.table("eta_cruda").select("*").range(offset, offset + limit - 1).execute()
    data = response.data
    
    if not data:
        break
        
    all_data.extend(data)
    offset += limit

df = pd.DataFrame(all_data)

st.dataframe(df)


# ===============================
# 2️⃣ SUBIR Y INSERTAR EXCEL
# ===============================

if st.button("Insertar en base de datos"):

    # Limpiar nombres de columnas (quitar espacios raros)
    df_nuevo.columns = df_nuevo.columns.str.strip()

    # Convertir NaN en None para Supabase
    df_nuevo = df_nuevo.where(pd.notnull(df_nuevo), None)

    datos = df_nuevo.to_dict(orient="records")

    # Insertar en bloques de 500
    batch_size = 500
    for i in range(0, len(datos), batch_size):
        batch = datos[i:i+batch_size]
        supabase.table("eta_cruda").insert(batch).execute()

    st.success("Datos insertados correctamente")




