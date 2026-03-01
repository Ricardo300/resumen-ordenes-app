import streamlit as st
from supabase import create_client
import pandas as pd
import unicodedata
from datetime import datetime, date

st.set_page_config(page_title="Base de datos ETA", layout="wide")
st.title("Base de datos ETA")

# ===============================
# 🔐 CONEXIÓN SUPABASE
# ===============================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

TABLE = "eta_cruda"

# ===============================
# 🧠 UTILIDADES
# ===============================
def norm_col(s: str) -> str:
    """Normaliza nombres para emparejar columnas aunque tengan acentos o caracteres raros."""
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))  # quita acentos
    # deja solo letras/números/_ (convierte espacios a _)
    out = []
    for c in s:
        if c.isalnum():
            out.append(c)
        elif c in [" ", "-", "/", "."]:
            out.append("_")
        # ignora otros símbolos raros
    s = "".join(out)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")

def to_jsonable(v):
    """Convierte valores de pandas/excel a tipos serializables en JSON."""
    if pd.isna(v):
        return None
    # pandas Timestamp
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime().isoformat()
    # datetime/date
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    # numpy types -> python
    try:
        import numpy as np
        if isinstance(v, (np.integer,)):
            return int(v)
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, (np.bool_,)):
            return bool(v)
    except Exception:
        pass
    # otros
    return v

def get_db_columns():
    """
    Obtiene los nombres reales de columnas de la tabla (tal como existen en Supabase),
    usando una fila de muestra.
    """
    r = supabase.table(TABLE).select("*").limit(1).execute()
    if r.data and len(r.data) > 0:
        return list(r.data[0].keys())
    # Si la tabla está vacía, al menos intenta con una selección (algunos drivers devuelven [])
    # En ese caso, no hay forma 100% confiable sin consultar information_schema.
    return []

# ===============================
# 📊 MOSTRAR BASE COMPLETA (PAGINADA)
# ===============================
st.subheader("Datos actuales en base (muestra paginada)")

col1, col2, col3 = st.columns([1,1,2])
with col1:
    limit = st.number_input("Filas por página", min_value=100, max_value=5000, value=1000, step=100)
with col2:
    page = st.number_input("Página", min_value=1, value=1, step=1)

offset = (page - 1) * limit
resp = supabase.table(TABLE).select("*").range(offset, offset + int(limit) - 1).execute()
df_view = pd.DataFrame(resp.data or [])
st.dataframe(df_view, use_container_width=True)

# ===============================
# 📤 SUBIR EXCEL E INSERTAR
# ===============================
st.subheader("Subir archivo ETA (Excel) y alimentar la base")

archivo = st.file_uploader("Seleccionar archivo Excel", type=["xlsx"])

if archivo is not None:
    df_nuevo = pd.read_excel(archivo, engine="openpyxl")
    st.write("Vista previa (primeras 20 filas):")
    st.dataframe(df_nuevo.head(20), use_container_width=True)

    if st.button("Insertar en base de datos"):
        # 1) Columnas reales en DB
        db_cols = get_db_columns()
        if not db_cols:
            st.error("No pude detectar columnas de la tabla (parece vacía y no devolvió esquema). Inserta 1 fila manual primero y vuelve a intentar.")
            st.stop()

        db_map = {norm_col(c): c for c in db_cols}  # normalizado -> real

        # 2) Emparejar columnas del Excel contra columnas reales DB
        excel_cols = list(df_nuevo.columns)
        rename = {}
        missing_in_db = []
        matched = []

        for c in excel_cols:
            key = norm_col(c)
            if key in db_map:
                rename[c] = db_map[key]
                matched.append((c, db_map[key]))
            else:
                missing_in_db.append(c)

        df_ready = df_nuevo.rename(columns=rename)

        # 3) Quedarse SOLO con columnas que existan en DB
        df_ready = df_ready[[c for c in df_ready.columns if c in db_cols]]

        # 4) Convertir valores a JSON-safe
        df_ready = df_ready.applymap(to_jsonable)

        # 5) Convertir a records
        datos = df_ready.to_dict(orient="records")

        st.info(f"Columnas detectadas en DB: {len(db_cols)} | Columnas del Excel: {len(excel_cols)} | Columnas que se insertarán: {len(df_ready.columns)}")

        if missing_in_db:
            st.warning("Estas columnas del Excel NO existen (con ese nombre) en la tabla y se ignorarán:")
            st.write(missing_in_db[:50])
            if len(missing_in_db) > 50:
                st.write(f"... y {len(missing_in_db)-50} más")

        # 6) Insert en batches + mostrar error real si ocurre
        batch_size = 500
        inserted = 0

        try:
            for i in range(0, len(datos), batch_size):
                batch = datos[i:i + batch_size]
                r = supabase.table(TABLE).insert(batch).execute()

                # si PostgREST devuelve error a veces viene en r.error
                if hasattr(r, "error") and r.error:
                    st.error("Error devuelto por Supabase/PostgREST:")
                    st.write(r.error)
                    st.stop()

                inserted += len(batch)

            st.success(f"✅ Insertadas {inserted} filas correctamente en '{TABLE}'.")

        except Exception as e:
            st.error("❌ Falló la inserción. Este es el error REAL capturado por la app:")
            st.exception(e)
            st.stop()

