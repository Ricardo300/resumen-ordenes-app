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
    # LIMPIAR NOMBRES DE COLUMNAS
    # ===============================
    df.columns = df.columns.str.strip().str.upper()

    st.subheader("Columnas detectadas")
    st.write(df.columns.tolist())

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

    # ===============================
    # FILTRAR COLUMNAS
    # ===============================
    df_materiales = df[columnas_necesarias].copy()

    # eliminar filas sin orden
    df_materiales = df_materiales.dropna(subset=["NUMERO DE ORDEN"])

    st.subheader("Datos preparados para guardar")
    st.dataframe(df_materiales.head(20))

    # ===============================
    # RENOMBRAR PARA BASE DE DATOS
    # ===============================
    df_db = df_materiales.rename(columns={
        "NUMERO DE ORDEN": "numero_orden",
        "MATERIAL": "material",
        "CANTIDAD": "cantidad",
        "SERIE": "serie",
        "MODELO": "modelo"
    }).copy()

    # ===============================
    # LIMPIAR TIPOS
    # ===============================
    df_db["numero_orden"] = df_db["numero_orden"].astype(str).str.strip()
    df_db["material"] = df_db["material"].astype(str).str.strip()
    df_db["cantidad"] = pd.to_numeric(df_db["cantidad"], errors="coerce")
    df_db["serie"] = df_db["serie"].where(pd.notnull(df_db["serie"]), None)
    df_db["modelo"] = df_db["modelo"].where(pd.notnull(df_db["modelo"]), None)

    # convertir NaN a None
    df_db = df_db.astype(object)
    df_db = df_db.where(pd.notnull(df_db), None)

    if st.button("Guardar materiales en base de datos"):

        try:
            # lista de órdenes limpia para el DELETE
            ordenes = (
                df_db["numero_orden"]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            # borrar materiales previos de esas órdenes
            if ordenes:
                supabase.table("materiales_ordenes") \
                    .delete() \
                    .in_("numero_orden", ordenes) \
                    .execute()

            # insertar materiales nuevos
            datos = df_db.to_dict(orient="records")

            supabase.table("materiales_ordenes") \
                .insert(datos) \
                .execute()

            st.success("Materiales cargados correctamente")

        except Exception as e:
            st.error(f"Error al guardar: {e}")
