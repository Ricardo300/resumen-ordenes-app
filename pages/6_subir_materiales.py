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

    # leer archivo
    df = pd.read_excel(archivo)

    # normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # mapear posibles nombres de columnas de ETA
    df = df.rename(columns={
        "numero de orden": "numero_orden",
        "número de orden": "numero_orden",
        "orden": "numero_orden",
        "solicitud": "numero_orden",
        "serie equipo": "serie"
    })

    # verificar columnas necesarias
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

    # QUEDARNOS SOLO CON LAS COLUMNAS NECESARIAS
    df = df[columnas_necesarias].copy()

    # limpiar serie vacía
    df["serie"] = df["serie"].fillna("SIN_SERIE")
    df["serie"] = df["serie"].replace("", "SIN_SERIE")
    df["serie"] = df["serie"].replace(" ", "SIN_SERIE")

    # limpiar nulos generales
    df = df.fillna("")

    # asegurar tipos correctos
    df["numero_orden"] = df["numero_orden"].astype(str).str.strip()
    df["material"] = df["material"].astype(str).str.strip()
    df["modelo"] = df["modelo"].astype(str).str.strip()
    df["serie"] = df["serie"].astype(str).str.strip()
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0)

    st.subheader("Vista previa del archivo")
    st.dataframe(df.head(20))

    if st.button("Guardar materiales en base de datos"):

        try:
            # convertir a registros JSON seguros
            datos = []
            for _, row in df.iterrows():
                datos.append({
                    "numero_orden": str(row["numero_orden"]),
                    "material": str(row["material"]),
                    "modelo": str(row["modelo"]),
                    "serie": str(row["serie"]),
                    "cantidad": float(row["cantidad"])
                })

            supabase.table("materiales_ordenes").upsert(
                datos,
                on_conflict="numero_orden,material,serie,modelo,cantidad"
            ).execute()

            st.success("Materiales cargados correctamente")

        except Exception as e:
            st.error(f"Error al guardar: {e}")
