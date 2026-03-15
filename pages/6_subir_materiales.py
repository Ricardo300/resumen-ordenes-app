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
    df_db["serie"] = df_db["serie"].astype(object)
    df_db["modelo"] = df_db["modelo"].astype(object)

    df_db = df_db.where(pd.notnull(df_db), None)

    # convertir a registros python puros
    datos = []
    for _, row in df_db.iterrows():
        datos.append({
            "numero_orden": None if row["numero_orden"] is None else str(row["numero_orden"]),
            "material": None if row["material"] is None else str(row["material"]),
            "cantidad": None if row["cantidad"] is None else float(row["cantidad"]),
            "serie": None if row["serie"] is None else str(row["serie"]),
            "modelo": None if row["modelo"] is None else str(row["modelo"]),
        })

    ordenes = sorted({d["numero_orden"] for d in datos if d["numero_orden"]})

    st.write("Órdenes detectadas:", len(ordenes))
    st.write("Primeras 10 órdenes:", ordenes[:10])
    st.write("Primeros 3 registros a insertar:")
    st.write(datos[:3])

    # ==========================================
    # PRUEBA 1: SOLO DELETE
    # ==========================================
    if st.button("Probar solo borrado"):

        try:
            # probar con pocas órdenes primero
            ordenes_prueba = ordenes[:20]

            if ordenes_prueba:
                supabase.table("materiales_ordenes") \
                    .delete() \
                    .in_("numero_orden", ordenes_prueba) \
                    .execute()

            st.success("Borrado ejecutado correctamente")

        except Exception as e:
            st.error(f"Error en borrado: {e}")

    # ==========================================
    # PRUEBA 2: SOLO INSERT
    # ==========================================
    if st.button("Probar solo insert"):

        try:
            datos_prueba = datos[:20]
            supabase.table("materiales_ordenes").insert(datos_prueba).execute()
            st.success("Insert ejecutado correctamente")

        except Exception as e:
            st.error(f"Error en insert: {e}")

    # ==========================================
    # CARGA COMPLETA
    # ==========================================
    if st.button("Guardar materiales en base de datos"):

        try:
            # 1. borrar primero solo las órdenes del archivo
            if ordenes:
                supabase.table("materiales_ordenes") \
                    .delete() \
                    .in_("numero_orden", ordenes) \
                    .execute()

            # 2. insertar todos los registros
            supabase.table("materiales_ordenes").insert(datos).execute()

            st.success("Materiales cargados correctamente")

        except Exception as e:
            st.error(f"Error al guardar: {e}")
