import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(layout="wide")
st.title("Carga de Materiales")

# ==========================================
# CONEXIÓN A SUPABASE
# ==========================================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ==========================================
# SUBIR ARCHIVO
# ==========================================

archivo = st.file_uploader("Subir archivo de materiales", type=["xlsx"])

if archivo is not None:

    # ===============================
    # LEER EXCEL
    # ===============================
    df = pd.read_excel(archivo)

    # ===============================
    # LIMPIAR COLUMNAS
    # ===============================
    df.columns = df.columns.str.strip().str.upper()

    st.subheader("Columnas detectadas")
    st.write(df.columns.tolist())

    st.subheader("Vista previa del archivo")
    st.dataframe(df.head())

    # ===============================
    # COLUMNAS NECESARIAS
    # ===============================
    columnas_necesarias = [
        "NUMERO DE ORDEN",
        "MATERIAL",
        "CANTIDAD",
        "SERIE",
        "MODELO"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            df[col] = None

    df_materiales = df[columnas_necesarias].copy()

    # eliminar filas sin orden
    df_materiales = df_materiales.dropna(subset=["NUMERO DE ORDEN"])

    st.subheader("Datos preparados")
    st.dataframe(df_materiales)

    # ===============================
    # RENOMBRAR COLUMNAS
    # ===============================
    df_db = df_materiales.rename(columns={
        "NUMERO DE ORDEN": "numero_orden",
        "MATERIAL": "material",
        "CANTIDAD": "cantidad",
        "SERIE": "serie",
        "MODELO": "modelo"
    })

    # convertir NaN a None
    df_db = df_db.astype(object)
    df_db = df_db.where(pd.notnull(df_db), None)

    # ===============================
    # BOTÓN GUARDAR
    # ===============================
    if st.button("Guardar materiales en base de datos"):

        try:

            # detectar órdenes únicas
            ordenes = df_db["numero_orden"].unique().tolist()

            # eliminar materiales anteriores de esas órdenes
            supabase.table("materiales_ordenes")\
                .delete()\
                .in_("numero_orden", ordenes)\
                .execute()

            # insertar nuevos materiales
            datos = df_db.to_dict(orient="records")

            supabase.table("materiales_ordenes")\
                .insert(datos)\
                .execute()

            st.success("Materiales cargados correctamente")

        except Exception as e:

            st.error(f"Error al guardar: {e}")
