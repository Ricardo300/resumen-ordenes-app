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

        # 🔍 Detectar columnas "Estado"
        columnas_estado = [col for col in df.columns if col.startswith("Estado")]

        if len(columnas_estado) < 2:
            st.error("No se detectaron las dos columnas 'Estado'")
            st.stop()

        estado_orden = columnas_estado[0]      # Estado de la orden
        estado_provincia = columnas_estado[1]  # Provincia

        # 🔥 Filtrar solo completadas
        df = df[
            df[estado_orden]
            .astype(str)
            .str.strip()
            .str.upper()
            == "COMPLETADO"
        ]

        # 🔥 Eliminar tiempos de almuerzo
        df = df[
            ~df["Tipo Actividad"]
            .astype(str)
            .str.strip()
            .isin(["Tiempo de almuerzo", "Tiempo Almuerzo LU"])
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

        # 🔄 Renombrar columnas
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

       # 🔄 Convertir fechas FORZANDO día primero (dd/mm/yyyy)

df["fecha"] = pd.to_datetime(
    df["fecha"],
    dayfirst=True,
    errors="coerce"
)

df["fecha_programacion"] = pd.to_datetime(
    df["fecha_programacion"],
    dayfirst=True,
    errors="coerce"
)

# 🚨 Validar que no haya fechas inválidas
if df["fecha"].isnull().any():
    st.error("Hay fechas inválidas en la columna Fecha.")
    st.stop()

# 🔄 Convertir a formato ISO seguro
df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")
df["fecha_programacion"] = df["fecha_programacion"].dt.strftime("%Y-%m-%d")
        # 🔄 Convertir horas a string 24h
        df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce").dt.strftime("%H:%M:%S")
        df["finalizacion"] = pd.to_datetime(df["finalizacion"], errors="coerce").dt.strftime("%H:%M:%S")

        # 🔄 Convertir timestamp completo
        df["hora_reserva_actividad"] = pd.to_datetime(
            df["hora_reserva_actividad"], errors="coerce"
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

        # 🔄 Limpiar NaN
        df = df.where(pd.notnull(df), None)

        st.write("Cantidad de registros a insertar:", len(df))
        st.write("Órdenes duplicadas en el archivo:", df["orden_trabajo"].duplicated().sum())

        if len(df) == 0:
            st.warning("No hay registros para insertar después del filtrado.")
            st.stop()

        datos = df.to_dict(orient="records")

        try:
            respuesta = supabase.table(TABLE).upsert(
                datos,
                on_conflict="orden_trabajo"
            ).execute()

            st.success("Datos insertados / actualizados correctamente")

        except Exception as e:
            st.error(f"Error al insertar: {e}")

