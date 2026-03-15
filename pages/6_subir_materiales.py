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

    # ===============================
    # PREPARAR DATAFRAME
    # ===============================

    df_materiales = df[columnas].copy()

    df_materiales = df_materiales.dropna(subset=["NUMERO DE ORDEN"])

    st.subheader("Datos preparados")
    st.dataframe(df_materiales.head(20))

    # ===============================
    # RENOMBRAR COLUMNAS
    # ===============================

    df_db = df_materiales.rename(columns={
        "NUMERO DE ORDEN": "numero_orden",
        "MATERIAL": "material",
        "CANTIDAD": "cantidad",
        "SERIE": "serie",
        "MODELO": "modelo"
    }).copy()

    # ===============================
    # LIMPIEZA DE TIPOS
    # ===============================

    df_db["numero_orden"] = df_db["numero_orden"].astype(str).str.strip()

    df_db["material"] = df_db["material"].astype(str).str.strip()

    df_db["cantidad"] = pd.to_numeric(df_db["cantidad"], errors="coerce")

    # corregir modelo que viene como 7006421.0
    df_db["modelo"] = df_db["modelo"].apply(
        lambda x: str(int(float(x))) if pd.notnull(x) else None
    )

    df_db["serie"] = df_db["serie"].apply(
        lambda x: str(x).strip() if pd.notnull(x) else None
    )

    # convertir NaN a None
    df_db = df_db.where(pd.notnull(df_db), None)

    # ===============================
    # CONVERTIR A JSON SEGURO
    # ===============================

    datos = []

    for _, row in df_db.iterrows():

        datos.append({
            "numero_orden": row["numero_orden"],
            "material": row["material"],
            "cantidad": float(row["cantidad"]) if row["cantidad"] is not None else None,
            "serie": row["serie"],
            "modelo": row["modelo"]
        })

    # ===============================
    # DETECTAR ORDENES
    # ===============================

    ordenes = sorted({d["numero_orden"] for d in datos if d["numero_orden"]})

    st.write("Órdenes detectadas:", len(ordenes))

    # ===============================
    # BOTON GUARDAR
    # ===============================

    if st.button("Guardar materiales en base de datos"):

        try:

            # eliminar materiales anteriores de esas órdenes
            if ordenes:
                supabase.table("materiales_ordenes") \
                    .delete() \
                    .in_("numero_orden", ordenes) \
                    .execute()

            # insertar materiales nuevos
            supabase.table("materiales_ordenes") \
                .insert(datos) \
                .execute()

            st.success("Materiales cargados correctamente")

        except Exception as e:

            st.error(f"Error al guardar: {e}")
