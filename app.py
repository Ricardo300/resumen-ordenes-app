import streamlit as st
from supabase import create_client
import pandas as pd

st.title("Prueba tabla simple ETA")

# 🔐 Conexión
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

TABLE = "eta_test"

# 📤 Subir Excel
archivo = st.file_uploader("Subir archivo Excel", type=["xlsx"])

if archivo is not None:

    df = pd.read_excel(archivo, engine="openpyxl")

    st.write("Vista previa del Excel:")
    st.dataframe(df.head())

    if st.button("Insertar en base de datos"):

        # 🔥 Nos quedamos SOLO con las 3 columnas
        columnas_necesarias = ["Técnico", "Fecha", "Estado"]

        # Verificar que existan en el Excel
        for col in columnas_necesarias:
            if col not in df.columns:
                st.error(f"No existe la columna {col} en el Excel")
                st.stop()

        df_filtrado = df[columnas_necesarias].copy()

        # Renombrar para que coincida con la tabla
        df_filtrado.columns = ["tecnico", "fecha", "estado"]

        # Limpiar NaN
        df_filtrado = df_filtrado.astype(object)
        df_filtrado = df_filtrado.where(pd.notnull(df_filtrado), None)

        datos = df_filtrado.to_dict(orient="records")

        # Insertar
        supabase.table(TABLE).insert(datos).execute()

        st.success("Datos insertados correctamente")

