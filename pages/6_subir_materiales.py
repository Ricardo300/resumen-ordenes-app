import streamlit as st
import pandas as pd
import numpy as np
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
# FUNCIÓN LIMPIAR JSON
# ==========================================

def limpiar_valor(v):

    if pd.isna(v):
        return None

    if isinstance(v, (np.integer)):
        return int(v)

    if isinstance(v, (np.floating)):
        return float(v)

    if isinstance(v, str):
        return v.strip()

    return v


# ==========================================
# SUBIR ARCHIVO
# ==========================================

archivo = st.file_uploader("Subir archivo de materiales", type=["xlsx"])

if archivo is not None:

    # ==========================================
    # LEER EXCEL
    # ==========================================

    df = pd.read_excel(archivo)

    # limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.upper()

    st.subheader("Columnas detectadas")
    st.write(df.columns.tolist())

    # ==========================================
    # COLUMNAS NECESARIAS
    # ==========================================

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

    # ==========================================
    # PREPARAR DATAFRAME
    # ==========================================

    df_materiales = df[columnas].copy()

    df_materiales = df_materiales.dropna(subset=["NUMERO DE ORDEN"])

    st.subheader("Vista previa")
    st.dataframe(df_materiales.head(20))

    # ==========================================
    # RENOMBRAR COLUMNAS
    # ==========================================

    df_db = df_materiales.rename(columns={
        "NUMERO DE ORDEN": "numero_orden",
        "MATERIAL": "material",
        "CANTIDAD": "cantidad",
        "SERIE": "serie",
        "MODELO": "modelo"
    }).copy()

    # ==========================================
    # LIMPIAR TIPOS
    # ==========================================

    df_db["numero_orden"] = df_db["numero_orden"].astype(str).str.strip()

    df_db["material"] = df_db["material"].astype(str).str.strip()

    df_db["cantidad"] = pd.to_numeric(df_db["cantidad"], errors="coerce")

    # eliminar .0 del modelo
    df_db["modelo"] = df_db["modelo"].apply(
        lambda x: str(int(float(x))) if pd.notnull(x) else None
    )

    df_db["serie"] = df_db["serie"].apply(
        lambda x: str(x).strip() if pd.notnull(x) else None
    )

    # ==========================================
    # CONVERTIR A JSON LIMPIO
    # ==========================================

    datos = []

    for _, row in df_db.iterrows():

        registro = {
            "numero_orden": limpiar_valor(row["numero_orden"]),
            "material": limpiar_valor(row["material"]),
            "cantidad": limpiar_valor(row["cantidad"]),
            "serie": limpiar_valor(row["serie"]),
            "modelo": limpiar_valor(row["modelo"])
        }

        datos.append(registro)

    # ==========================================
    # MOSTRAR JSON PARA DEBUG
    # ==========================================

    st.subheader("JSON generado (debug)")
    st.json(datos[:10])

    # ==========================================
    # DETECTAR ORDENES
    # ==========================================

    ordenes = list({d["numero_orden"] for d in datos if d["numero_orden"]})

    st.write("Órdenes detectadas:", len(ordenes))

    # ==========================================
    # BOTON GUARDAR
    # ==========================================

    if st.button("Guardar materiales en base de datos"):

        try:

            # borrar registros anteriores
            if ordenes:
                supabase.table("materiales_ordenes") \
                    .delete() \
                    .in_("numero_orden", ordenes) \
                    .execute()

            # insertar nuevos registros
            supabase.table("materiales_ordenes") \
                .insert(datos) \
                .execute()

            st.success("Materiales guardados correctamente")

        except Exception as e:

            st.error(f"Error al guardar: {e}")
