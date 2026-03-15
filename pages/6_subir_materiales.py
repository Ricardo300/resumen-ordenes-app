import pandas as pd

# ruta del archivo
archivo = "materiales.xlsx"

# leer excel
df = pd.read_excel(archivo)

# ver columnas
print("COLUMNAS DEL ARCHIVO:")
print(df.columns)

# ver primeras filas
print("\nPRIMERAS FILAS:")
print(df.head())
