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
    # VERIFICAR DUPLICADOS SEGÚN CLAVE UPSERT
    # ==========================================
    
    df_check = df.groupby(
        ["numero_orden", "material", "modelo", "serie", "cantidad"]
    ).size().reset_index(name="conteo")
    
    duplicados = df_check[df_check["conteo"] > 1]
    
    st.subheader("Diagnóstico de duplicados")
    
    st.write("Filas totales en archivo:", len(df))
    
    if len(duplicados) == 0:
        st.success("No se detectaron duplicados según la clave de conflicto")
    else:
        st.error(f"Se detectaron {len(duplicados)} combinaciones duplicadas")
        st.dataframe(duplicados)
        
        st.subheader("Vista previa")
        st.dataframe(df.head(20))

    if st.button("Guardar materiales en base de datos"):

        try:

            # contar antes
            conteo_antes = supabase.table("materiales_ordenes") \
                .select("*", count="exact") \
                .execute().count

            registros_archivo = len(df)

            # convertir a JSON seguro
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
            duplicados = registros_archivo - insertados

            st.success("Carga completada")

            st.write(f"Registros en archivo: {registros_archivo}")
            st.write(f"Insertados nuevos: {insertados}")
            st.write(f"Duplicados ignorados: {duplicados}")
            st.write(f"Total en base: {conteo_despues}")

        except Exception as e:
            st.error(f"Error al guardar: {e}")
