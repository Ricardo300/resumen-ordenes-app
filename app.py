import streamlit as st
from supabase import create_client
import pandas as pd

st.title("Carga KPI ETA")

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

TABLE = "kpi_ordenes_completadas"

archivo = st.file_uploader("Subir archivo Excel", type=["xlsx"])

if archivo is not None:

    df = pd.read_excel(archivo, engine="openpyxl")

    if st.button("Insertar en base de datos"):

        # 🔥 Filtrar solo completadas (primer Estado)
        df = df[df["Estado"] == "Completado"]

        # 🔥 Eliminar tiempos de almuerzo
        df = df[
            ~df["Tipo Actividad"].isin(
                ["Tiempo de almuerzo", "Tiempo Almuerzo LU"]
            )
        ]

        # 🔥 Seleccionar columnas necesarias
        columnas_necesarias = [
            "Orden de Trabajo",
            "Identificador Tecnico",
            "Identidad",
            "Fecha",
            "Estado.1",  # ← Segundo Estado = Provincia
            "Municipio/Canton",
            "Colonia",
            "Sub Tipo de Orden",
            "Tipo Actividad",
            "Garantia",
            "Inicio",
            "Finalización",
            "Hora de reserva de actividad",
            "Fecha Programación"
        ]

        df = df[columnas_necesarias].copy()

        # 🔥 Renombrar columnas
        df.columns = [
            "orden_trabajo",
            "identificador_tecnico",
            "identidad",
            "fecha",
            "provincia",
            "municipio_canton",
            "colonia",
            "sub_tipo_orden",
            "tipo_actividad",
            "garantia",
            "inicio",
            "finalizacion",
            "hora_reserva_actividad",
            "fecha_programacion"
        ]

        # 🔥 Convertir tipos
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
        df["fecha_programacion"] = pd.to_datetime(
            df["fecha_programacion"], errors="coerce"
        ).dt.date

        df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce").dt.time
        df["finalizacion"] = pd.to_datetime(df["finalizacion"], errors="coerce").dt.time

        df["hora_reserva_actividad"] = pd.to_datetime(
            df["hora_reserva_actividad"], errors="coerce"
        )

        # Limpiar NaN
        df = df.astype(object)
        df = df.where(pd.notnull(df), None)

        datos = df.to_dict(orient="records")

        supabase.table(TABLE).insert(datos).execute()

        st.success("Datos insertados correctamente")
