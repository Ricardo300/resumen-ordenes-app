import streamlit as st
from supabase import create_client
import pandas as pd

st.title("Base de datos ETA")
archivo = st.file_uploader("Subir archivo ETA (Excel)", type=["xlsx"])
if archivo is not None:
    df_nuevo = pd.read_excel(archivo, engine="openpyxl")
    st.write("Vista previa del archivo cargado:")
    st.dataframe(df_nuevo.head())
    
    if st.button("Insertar en base de datos"):
    datos = df_nuevo.to_dict(orient="records")
    supabase.table("eta_cruda").insert(datos).execute()
    st.success("Datos insertados correctamente")

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

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




