import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(layout="wide")
st.title("Carga de Materiales")

# conexión a supabase
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

archivo = st.file_uploader(
    "Subir archivo de materiales",
    type=["xlsx"]
)

if archivo is not None:

    df = pd.read_excel(archivo)

    # normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # mapear nombres posibles
    df = df.rename(columns={
        "numero de orden": "numero_orden",
        "número de orden": "numero_orden",
        "orden": "numero_orden",
        "solicitud": "numero_orden",
        "serie equipo": "serie"
    })

    columnas_necesarias = [
        "numero_orden",
        "material",
        "modelo",
        "serie",
        "cantidad"
    ]

    for col in columnas_necesarias:
        if col not in df.columns:
            st.error(f"Falta la columna: {col}")
            st.write("Columnas detectadas:", df.columns.tolist())
            st.stop()

    # quedarnos solo con columnas necesarias
    df = df[columnas_necesarias].copy()

    # limpiar serie
    df["serie"] = df["serie"].fillna("SIN_SERIE")
    df["serie"] = df["serie"].replace("", "SIN_SERIE")

    # limpiar nulos
    df = df.fillna("")

    # tipos
    df["numero_orden"] = df["numero_orden"].astype(str)
    df["material"] = df["material"].astype(str)
    df["modelo"] = df["modelo"].astype(str)
    df["serie"] = df["serie"].astype(str)
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0)

    # ==========================================
    # 📊 CONTROL DE DUPLICADOS (ANTES DE LIMPIAR)
    # ==========================================

    filas_originales = len(df)

    df_check = df.groupby(
        ["numero_orden", "material", "modelo", "serie", "cantidad"]
    ).size().reset_index(name="conteo")

    duplicados_df = df_check[df_check["conteo"] > 1]

    cantidad_duplicados = duplicados_df["conteo"].sum() - len(duplicados_df)

    # ==========================================
    # 🔧 LIMPIAR DUPLICADOS
    # ==========================================

    df = df.drop_duplicates(
        subset=["numero_orden","material","modelo","serie","cantidad"]
    )

    filas_finales = len(df)

    # ==========================================
    # 📢 MOSTRAR RESULTADOS
    # ==========================================

    st.subheader("Control de calidad de datos")

    st.write("Filas en archivo:", filas_originales)
    st.write("Duplicados detectados:", cantidad_duplicados)
    st.write("Duplicados eliminados:", filas_originales - filas_finales)
    st.write("Filas finales a insertar:", filas_finales)

    if cantidad_duplicados > 0:
        st.warning("Se detectaron duplicados en el archivo. Fueron eliminados automáticamente.")

    st.subheader("Vista previa")
    st.dataframe(df.head(20))

    # ==========================================
    # 🚀 GUARDAR EN BASE DE DATOS
    # ==========================================

    if st.button("Guardar materiales en base de datos"):

        try:

            # contar antes
            conteo_antes = supabase.table("materiales_ordenes") \
                .select("*", count="exact") \
                .execute().count

            registros_archivo = len(df)

            datos = df.to_dict(orient="records")

            supabase.table("materiales_ordenes").upsert(
                datos,
                on_conflict="numero_orden,material,serie,modelo,cantidad"
            ).execute()

            # contar después
            conteo_despues = supabase.table("materiales_ordenes") \
                .select("*", count="exact") \
                .execute().count

            insertados = conteo_despues - conteo_antes
            duplicados_bd = registros_archivo - insertados

            st.success("Carga completada")

            st.write(f"Registros enviados: {registros_archivo}")
            st.write(f"Insertados nuevos: {insertados}")
            st.write(f"Duplicados en base ignorados: {duplicados_bd}")
            st.write(f"Total en base: {conteo_despues}")

        except Exception as e:
            st.error(f"Error al guardar: {e}")
