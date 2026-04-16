import os
import streamlit as st

st.set_page_config(page_title="Cargar Archivo ETA", layout="wide")

RUTA_ARCHIVO_FIJO = "/tmp/dashboard_eta_actual.xlsx"

st.title("Cargar Archivo ETA")

st.markdown("Sube aquí el archivo que quedará activo para el dashboard del TV.")

archivo = st.file_uploader("Selecciona archivo Excel", type=["xlsx", "xls"])

if archivo is not None:
    with open(RUTA_ARCHIVO_FIJO, "wb") as f:
        f.write(archivo.getvalue())

    st.success(f"Archivo guardado correctamente: {archivo.name}")

if os.path.exists(RUTA_ARCHIVO_FIJO):
    st.info(f"Archivo activo actual: {os.path.basename(RUTA_ARCHIVO_FIJO)}")
else:
    st.warning("Todavía no hay archivo cargado.")
