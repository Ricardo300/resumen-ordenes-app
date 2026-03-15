import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(layout="wide")
st.title("Carga de Materiales")

# ==========================================
# CONEXIÓN SUPABASE
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

    df = pd.read_excel(archivo)

    # limpiar nombres columnas
    df.columns = df.columns.str.strip().str.upper()

    st.subheader("Columnas detectadas")
    st.write(df.columns.tolist())

    st.subheader("Vista previa")
    st.dataframe(df.head())

    columnas = [
        "NUMERO DE ORDEN",
        "MATERIAL",
        "CANTIDAD",
        "SERIE",
        "MODELO"
    ]

    for col in columnas:
        if col not in df.columns:
            df[col] = None

    df_materiales = df[columnas].copy()
    df_materiales = df_materiales.dropna(subset=["NUMERO DE ORDEN"])

    st.subheader("Datos preparados")
    st.dataframe(df_materiales)

    # ==========================================
    # RENOMBRAR PARA BASE
    # ==========================================

    df_db = df_materiales.rename(columns={
        "NUMERO DE ORDEN": "numero_orden",
        "MATERIAL": "material",
        "CANTIDAD": "cantidad",
        "SERIE": "serie",
        "MODELO": "modelo"
    })

    # ==========================================
    # LIMPIEZA TOTAL PARA JSON
    # ==========================================

    df_db = df_db.replace({pd.NA: None})
    df_db = df_db.replace({float("nan"): None})
    df_db = df_db.astype(object)

    # convertir todo a tipos python
    df_db["numero_orden"] = df_db["numero_orden"].astype(str)
    df_db["material"] = df_db["material"].astype(str)
    df_db["modelo"] = df_db["modelo"].astype(str)

    if st.button("Guardar materiales en base de datos"):

        try:

            # detectar órdenes únicas
            ordenes = df_db["numero_orden"].unique().tolist()

            # eliminar materiales anteriores
            supabase.table("materiales_ordenes")\
                .delete()\
                .in_("numero_orden", ordenes)\
                .execute()

            datos = df_db.to_dict(orient="records")

            # insertar nuevos materiales
            supabase.table("materiales_ordenes")\
                .insert(datos)\
                .execute()

            st.success("Materiales cargados correctamente")

        except Exception as e:

            st.error(f"Error al guardar: {e}")
