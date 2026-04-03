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

    # ==========================================
    # NORMALIZACIÓN FUERTE
    # ==========================================

    df["numero_orden"] = (
        df["numero_orden"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["material"] = (
        df["material"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["serie"] = (
        df["serie"]
        .fillna("SIN_SERIE")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    df.loc[df["serie"] == "", "serie"] = "SIN_SERIE"
    df.loc[df["serie"] == "NAN", "serie"] = "SIN_SERIE"
    df.loc[df["serie"] == "NONE", "serie"] = "SIN_SERIE"

    # MODELO:
    # convierte 4018238 y 4018238.0 al mismo valor "4018238"
    # y si viene vacío o inválido lo deja como SIN_MODELO
    df["modelo"] = pd.to_numeric(df["modelo"], errors="coerce")
    df["modelo"] = df["modelo"].apply(
        lambda x: "SIN_MODELO" if pd.isna(x) else str(int(x))
    )

    # CANTIDAD:
    # convierte a número y elimina registros con cantidad <= 0
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce").fillna(0)
    df["cantidad"] = df["cantidad"].astype(int)

    filas_originales = len(df)

    # eliminar registros con cantidad inválida
    df_eliminadas_cantidad = df[df["cantidad"] <= 0].copy()
    df = df[df["cantidad"] > 0].copy()

    eliminadas_por_cantidad = len(df_eliminadas_cantidad)

    # ==========================================
    # VALIDACIONES DE CALIDAD
    # ==========================================

    errores = pd.DataFrame()

    errores_numero_orden = df[df["numero_orden"] == ""].copy()
    if not errores_numero_orden.empty:
        errores_numero_orden["error"] = "numero_orden vacío"

    errores_material = df[df["material"] == ""].copy()
    if not errores_material.empty:
        errores_material["error"] = "material vacío"

    errores = pd.concat(
        [
            errores_numero_orden,
            errores_material
        ],
        ignore_index=True
    )

    if not errores.empty:
        errores = errores.drop_duplicates()

    # ==========================================
    # CONTROL DE DUPLICADOS
    # ==========================================

    df_check = df.groupby(
        ["numero_orden", "material", "modelo", "serie", "cantidad"]
    ).size().reset_index(name="conteo")

    duplicados_df = df_check[df_check["conteo"] > 1]

    cantidad_duplicados = (
        duplicados_df["conteo"].sum() - len(duplicados_df)
        if not duplicados_df.empty else 0
    )

    # eliminar duplicados ya normalizados
    df = df.drop_duplicates(
        subset=["numero_orden", "material", "modelo", "serie", "cantidad"]
    )

    filas_finales = len(df)

    # ==========================================
    # MOSTRAR RESULTADOS
    # ==========================================

    st.subheader("Control de calidad de datos")

    st.write("Filas en archivo:", filas_originales)
    st.write("Registros eliminados por cantidad inválida:", eliminadas_por_cantidad)
    st.write("Duplicados detectados:", cantidad_duplicados)
    st.write("Duplicados eliminados:", (filas_originales - eliminadas_por_cantidad) - filas_finales)
    st.write("Filas finales a insertar:", filas_finales)

    if eliminadas_por_cantidad > 0:
        st.warning("Se eliminaron registros con cantidad menor o igual a 0.")

    if cantidad_duplicados > 0:
        st.warning("Se detectaron duplicados en el archivo. Fueron eliminados automáticamente.")

    if not errores.empty:
        st.error("Se detectaron registros inválidos. La carga será bloqueada hasta corregirlos.")
        st.subheader("Registros con error")
        st.dataframe(errores, use_container_width=True)

    st.subheader("Vista previa")
    st.dataframe(df.head(20), use_container_width=True)

    # ==========================================
    # GUARDAR EN BASE DE DATOS
    # ==========================================

    if st.button("Guardar materiales en base de datos"):

        if not errores.empty:
            st.error("No se puede guardar porque hay registros inválidos en el archivo.")
            st.stop()

        try:
            conteo_antes = (
                supabase.table("materiales_ordenes")
                .select("*", count="exact")
                .execute()
                .count
            )

            registros_archivo = len(df)

            datos = df.to_dict(orient="records")

            supabase.table("materiales_ordenes").upsert(
                datos,
                on_conflict="numero_orden,material,serie,modelo,cantidad"
            ).execute()

            conteo_despues = (
                supabase.table("materiales_ordenes")
                .select("*", count="exact")
                .execute()
                .count
            )

            insertados = conteo_despues - conteo_antes
            duplicados_bd = registros_archivo - insertados

            st.success("Carga completada")
            st.write(f"Registros enviados: {registros_archivo}")
            st.write(f"Insertados nuevos: {insertados}")
            st.write(f"Duplicados en base ignorados: {duplicados_bd}")
            st.write(f"Total en base: {conteo_despues}")

        except Exception as e:
            st.error(f"Error al guardar: {e}")
