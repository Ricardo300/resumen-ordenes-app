import streamlit as st
from supabase import create_client
import pandas as pd

st.title("Carga KPI ETA")

# 🔐 Conexión Supabase
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

TABLE = "kpi_ordenes_completadas"

archivo = st.file_uploader("Subir archivo Excel", type=["xlsx"])

if archivo is not None:

    df = pd.read_excel(archivo, engine="openpyxl")

# ==========================================
# 🔧 REGLA DE NEGOCIO - MantenimientoPX es GPON
# ==========================================

df["tipo_actividad"] = df["tipo_actividad"].astype(str).str.strip()

df.loc[
    df["tipo_actividad"].str.upper().eq("MANTENIMIENTOPX"),
    "tecnologia"
] = "GPON"

    if st.button("Insertar en base de datos"):

        # ============================================
        # 🔎 Detectar columnas Estado
        # ============================================

        columnas_estado = [col for col in df.columns if col.startswith("Estado")]

        if len(columnas_estado) < 2:
            st.error("No se detectaron las dos columnas 'Estado'")
            st.stop()

        estado_orden = columnas_estado[0]
        estado_provincia = columnas_estado[1]

        # ============================================
        # 🔥 Filtrar solo COMPLETADO
        # ============================================

        df = df[
            df[estado_orden]
            .astype(str)
            .str.strip()
            .str.upper()
            == "COMPLETADO"
        ]

        # ============================================
        # 🔥 Eliminar tiempos de almuerzo
        # ============================================

        df = df[
            ~df["Tipo Actividad"]
            .astype(str)
            .str.strip()
            .isin(["Tiempo de almuerzo", "Tiempo Almuerzo LU"])
        ]

        # ============================================
        # 📌 Columnas necesarias
        # ============================================

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

        # ============================================
        # 🔄 Renombrar columnas
        # ============================================

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

        # ============================================
        # 🔥 CLASIFICAR TECNOLOGÍA
        # ============================================

        map_tecnologia = {

            # DTH
            "Cambio de Plan con Cambio de Equipo DTH": "DTH",
            "Equipo Adicional TV": "DTH",
            "Instalación de Cajas Adicionales DTH": "DTH",
            "Instalación de servicio televisión DTH": "DTH",
            "Instalación de TV (DTH)": "DTH",
            "Cambio de Equipo TV":"DTH",
            "Reparacion DTH": "DTH",
            "Reparacion Linea Fija LFI": "DTH",
            "Reparación servicio DTH": "DTH",
            "Traslado Externo de TV (DTH)": "DTH",
            "Traslado Interno de Servicio de DTH": "DTH",
            "Traslado Interno de TV (DTH)": "DTH",
            "Traslado TV (DTH)": "DTH",

            # GPON
            "Cambio de Plan con Cambio de Equipo Datos y TV": "GPON",
            "Cambio de Plan con Cambio de Equipo Triple Play": "GPON",
            "Equipo Adicional Datos": "GPON",
            "Equipo Adicional Datos y TV": "GPON",
            "Equipo Adicional Triple Play": "GPON",
            "Instalacion Internet (DGPON)+TV (GPON)": "GPON",
            "Instalacion Internet (GPON)": "GPON",
            "Instalacion Línea fija (VGPON) + Internet (DGPON)": "GPON",
            "Instalacion Línea fija (VGPON) + Internet (DGPON)+TV (GPON)": "GPON",
            "Reparación Internet (DGPON) + TV (GPON)": "GPON",
            "Reparación Internet (GPON)": "GPON",
            "Reparación Línea fija (VGPON) + Internet (DGPON)":"GPON",
            "Reparación Línea fija (VGPON) + Internet (DGPON)+TV (GPON)": "GPON",
            "Traslado Externo Internet (DGPON) + TV (GPON)": "GPON",
            "Traslado Externo Internet (GPON)": "GPON",
            "Traslado Externo Línea fija (VGPON) + Internet (DGPON)": "GPON",
            "Traslado Externo Línea fija (VGPON) + Internet (DGPON)+TV (GPON)": "GPON",
            "Traslado Interno de Internet (GPON) + TV (GPON)": "GPON",
            "Traslado Interno Internet (GPON)": "GPON",
            "Traslado Interno Linea fIja (GPON) + Internet (GPON)": "GPON",
            "Traslado Interno Linea fIja (GPON) + Internet (GPON) + TV (GPON)": "GPON",
        }

        df["tecnologia"] = df["sub_tipo_orden"].map(map_tecnologia)
        df["tecnologia"] = df["tecnologia"].fillna("NO_CLASIFICADO")
        # ============================================
        # 🔥 AGREGAR CONTRATA DESDE TABLA AUXILIAR
        # ============================================

        respuesta = supabase.table("tabla_tecnicos_contrata").select("*").execute()
        df_contrata = pd.DataFrame(respuesta.data)

        # Limpiar posibles espacios
        df_contrata["identificador_tecnico"] = df_contrata["identificador_tecnico"].str.strip()
        df["identificador_tecnico"] = df["identificador_tecnico"].str.strip()

        # Merge
        df = df.merge(
        df_contrata,
        on="identificador_tecnico",
        how="left"
        )

        df["contrata"] = df["contrata"].fillna("NO_ASIGNADO")
        # ============================================
        # 🔄 CONVERTIR FECHAS CORRECTAMENTE
        # ============================================

        df["fecha"] = pd.to_datetime(
            df["fecha"],
            errors="coerce",
            dayfirst=True
        ).dt.strftime("%Y-%m-%d")

        df["fecha_programacion"] = pd.to_datetime(
            df["fecha_programacion"],
            errors="coerce",
            dayfirst=True
        ).dt.strftime("%Y-%m-%d")

        df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce").dt.strftime("%H:%M:%S")
        df["finalizacion"] = pd.to_datetime(df["finalizacion"], errors="coerce").dt.strftime("%H:%M:%S")

        df["hora_reserva_actividad"] = pd.to_datetime(
            df["hora_reserva_actividad"],
            errors="coerce",
            dayfirst=True
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

        # ============================================
        # 🔄 Limpiar NaN
        # ============================================

        df = df.where(pd.notnull(df), None)

        st.write("Cantidad de registros a insertar:", len(df))
        st.write("Órdenes duplicadas en archivo:", df["orden_trabajo"].duplicated().sum())

        if len(df) == 0:
            st.warning("No hay registros para insertar.")
            st.stop()

        datos = df.to_dict(orient="records")

        try:
            supabase.table(TABLE).upsert(
                datos,
                on_conflict="orden_trabajo"
            ).execute()

            st.success("Datos insertados / actualizados correctamente")

        except Exception as e:
            st.error(f"Error al insertar: {e}")





