import streamlit as st
from supabase import create_client
import pandas as pd

st.title("Carga KPI ETA")

# 🔐 Conexión
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

TABLE = "kpi_ordenes_completadas"

archivo = st.file_uploader("Subir archivo Excel", type=["xlsx"])

if archivo is not None:

    df = pd.read_excel(archivo, engine="openpyxl")

    if st.button("Insertar en base de datos"):

        # 🔍 Detectar columnas duplicadas "Estado"
        columnas_estado = [col for col in df.columns if col.startswith("Estado")]

        if len(columnas_estado) < 2:
            st.error("No se detectaron las dos columnas 'Estado'")
            st.stop()

        estado_orden = columnas_estado[0]      # Estado de la orden
        estado_provincia = columnas_estado[1]  # Provincia

        # 🔥 Filtrar solo completadas (robusto)
        df = df[df[estado_orden].astype(str).str.strip().str.upper() == "COMPLETADO"]

        # 🔥 Eliminar tiempos de almuerzo
        df = df[
            ~df["Tipo Actividad"].astype(str).str.strip().isin(
                ["Tiempo de almuerzo", "Tiempo Almuerzo LU"]
            )
        ]

        # 🔥 Seleccionar columnas necesarias
        columnas_necesarias = [
            "Orden de Trabajo",
            "Identificador Tecnico",
            "Identidad",
            "Fecha",
            estado_provincia,
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

        for col in columnas_necesarias:
            if col not in df.columns:
                st.error(f"No existe la columna {col} en el Excel")
                st.stop()

        df = df[columnas_necesarias].copy()

        # 🔄 Renombrar columnas para Supabase
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

        # 🔄 Convertir fechas
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.date
        df["fecha_programacion"] = pd.to_datetime(
            df["fecha_programacion"], errors="coerce"
        ).dt.date

        # 🔄 Convertir horas (soporta 12h y 24h mezclado)
        df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce").dt.time
        df["finalizacion"] = pd.to_datetime(df["finalizacion"], errors="coerce").dt.time

        # 🔄 Convertir timestamp completo
        df["hora_reserva_actividad"] = pd.to_datetime(
            df["hora_reserva_actividad"], errors="coerce"
        )

        # 🔄 Limpiar NaN
        df = df.astype(object)
        df = df.where(pd.notnull(df), None)

        st.write("Cantidad de registros a insertar:", len(df))

        if len(df) == 0:
            st.warning("No hay registros para insertar después del filtrado.")
            st.stop()

        datos = df.to_dict(orient="records")

        respuesta = supabase.table(TABLE).insert(datos).execute()

        if hasattr(respuesta, "error") and respuesta.error:
            st.error(f"Error al insertar: {respuesta.error}")
        else:
            st.success("Datos insertados correctamente")
