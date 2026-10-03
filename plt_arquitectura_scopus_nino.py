# -*- coding: utf-8 -*-
"""
Created on Tue Jul 21 17:16:08 2026

@author: Enzo
"""

###############################################################################
# PROYECTO PARA LA ARQUITECTURA Y EL TRATAMIENTO DE LOS DATOS DE MI ANÁLISIS
###############################################################################

#OBJETIVO: Realizar una arquitectura de datos

# Se importan las librerias a utilizar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import unicodedata
from itertools import zip_longest
import re

# Se carga el archivo que contiene información de scopus de publicaciones científicas en torno al fenómeno El Niñó en donde al
# al menos un investigador consignó como afiliación a una entidad peruana en formato csv y
# se convierte en un objeto dataframe

#investiga = pd.read_csv("scopus_export_Jul 20-2026_ced6233f-1ae9-4552-96e3-f7b043495d28.csv", engine="python", encoding="utf-8", sep=",")
investiga = pd.read_csv("scopus_export_Aug 10-2026_2a008413-4d75-4a40-82af-92a2abe78387.csv", engine="python", encoding="utf-8", sep=",")


# Se realiza una análisis del dataframe investiga
investiga.shape
investiga.columns
investiga.dtypes
investiga.info()

# Se renombran algunas columnas del dataframe investiga
investiga.rename(columns=({"Document Type":"Document_type"}), inplace=True)

# Se identifica la presencia de duplicados en el dataframe investiga
duplicado = investiga.duplicated(subset=["EID"])
print("¿Existe la presencia de duplicados?:", duplicado.any())


# Se eliminan categorias de la columna Document_type
categorias_excluir = [
    "Letter",
    "Editorial",
    "Erratum",
    "Note",
    "Short survey"
]

investiga = investiga[
    ~investiga["Document_type"].isin(categorias_excluir)
].copy()


# Se reestructura investiga considerando como unidad de análisis la publicación científica
investiga = investiga[["EID", "DOI", "Title", "Year", "Cited by", "Document_type","Cited by","Author full names", "Authors with affiliations"]]

# Se realiza por segunda vez una análisis del dataframe investiga con las variaciones hechas
investiga.shape
investiga.columns
investiga.dtypes
investiga.info()

# Se analiza la distribución de las publicaciones científicas (2010 - 2024) considerando el tipo de documento, desde una dimensión absoluta y proporcional
investiga.Document_type.value_counts()
(investiga["Document_type"]
 .value_counts(normalize=True)
 .mul(100)
 .round(1))


# Se analiza la distribución de las publicaciones científicas (2010 - 2024) considerando el publisher, desde una dimensión absoluta y proporcional
#investiga.Publisher.value_counts()
#(investiga["Publisher"]
 #.value_counts(normalize=True)
 #.mul(100)
 #.round(1))


# se realiza una distribución de cantidad de publicaciones científicas por año
investiga_año = investiga.groupby("Year")["EID"].count()
investiga_año = investiga_año.to_frame()
investiga_año.reset_index(inplace=True)

# Se analiza los tipos de datos de las columnas que conforman el dataframe investiga_año
investiga_año.info()

# Se renombra la columna EID del dataframe investiga_año
investiga_año.rename(columns=({"EID":"Cantidad", "Year":"Año"}), inplace=True)

# Se cambian los atributos a tipo númerico
investiga_año["Año"] = pd.to_numeric(investiga_año["Año"], errors="coerce")
investiga_año["Cantidad"] = pd.to_numeric(investiga_año["Cantidad"], errors="coerce")

investiga_año = investiga_año.sort_values("Año")

# Colores institucionales
color_principal = "#00A7B5"   # turquesa
color_secundario = "#5FB7C6"  # azul petróleo

# Tamaño más amplio (clave para separar barras)
plt.figure(figsize=(12,6))

# Crear barras con menor ancho (más espacio)
bars = plt.bar(investiga_año["Año"], investiga_año["Cantidad"], 
               color=color_principal, 
               width=0.6)

# Etiquetas
plt.xlabel("Año", fontsize=11, color="black")
plt.ylabel("Cantidad de publicaciones", fontsize=11, color="black")

# Título más sobrio (tipo consultoría)
#plt.title("Evolución de contratos por año", 
          #fontsize=13, 
          #color=color_secundario, 
          #pad=15)

# Quitar bordes innecesarios
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Suavizar ejes
ax.spines["left"].set_color("#CCCCCC")
ax.spines["bottom"].set_color("#CCCCCC")

# Grid ligero (muy consultoría)
plt.grid(axis='y', linestyle='--', alpha=0.3)

años = investiga_año["Año"].dropna().astype(int).tolist()
ax.set_xticks(años)
ax.set_xticklabels([str(a) for a in años], rotation=0)

# Etiquetas
for x, y in zip(investiga_año["Año"], investiga_año["Cantidad"]):
    #if pd.notna(x) and pd.notna(y) and y > 100:
        plt.text(
            float(x),
            float(y),
            f"{int(y)}",
            ha="center",
            va="bottom",
            fontsize=14,
            color=color_principal
        )

# Margen superior para que no choque texto
plt.ylim(0, investiga_año["Cantidad"].max())

plt.tight_layout()
plt.show()


investiga.columns
caso = investiga[investiga["EID"]=="2-s2.0-85088879419"]

# Se construye el dataframe df_autores, el cual tiene como unidad de análisis la publicación científica
# mostrando para cada uno el código scopus y el nombre del autor
filas = []
pat = re.compile(r"^(.*)\s*\((\d+)\)\s*$") # "Takahashi, Ken (55763471100)"

for _, fila in investiga.iterrows():
    raw_full = fila.get("Author full names")
    raw_aff = fila.get("Authors with affiliations")

    full_list = [x.strip() for x in str(raw_full).split(";") if x.strip() and x.strip().lower()!= "nan"] if pd.notna(raw_full) else []
    aff_list = [x.strip() for x in str(raw_aff).split(";") if x.strip() and x.strip().lower()!= "nan"] if pd.notna(raw_aff) else []

    for full_entry, aff_block in zip_longest(full_list, aff_list, fillvalue=""):
        if not full_entry:
            continue

        m = pat.match(full_entry)
        if m:
            nombre = m.group(1).strip()
            author_id = m.group(2).strip()
        else:
            nombre = full_entry
            author_id = ""

        # afiliación = todo después de la primera coma: "Takahashi K., Instituto..."
        affiliation = aff_block.split(",", 1)[1].strip() if "," in aff_block else aff_block.strip()

        filas.append({
            "EID": fila.get("EID"),
            "Year": fila.get("Year"),
            "Author_id": author_id,
            "Author_name": nombre,
            "Affiliations": affiliation,
            "Aff_block_raw": aff_block # déjalo para debug de tus 9 masivas
        })

df_autores = pd.DataFrame(filas)
df_autores = df_autores[df_autores["Author_id"]!= ""]

df_nodos = df_autores.sort_values("Year").drop_duplicates("Author_id", keep="first")[["Author_id","Author_name","Affiliations"]]

print("df_autores:", len(df_autores), "nodos:", len(df_nodos))
print("Year min-max:", df_autores["Year"].min(), "-", df_autores["Year"].max())


# Considerando el dataframe df_autores, se construye la tabla de nodos y la tabla de autor publicación
df_nodos = (
    df_autores
    .sort_values("Year")
    .drop_duplicates("Author_id")
    [["Author_id","Author_name","Affiliations"]]
)


# tabla df_autor_publicacion
df_autor_publicacion = df_autores[["EID", "Year", "Author_id"]]


# Guardar tabla de autores en un archivo csv
df_nodos.to_csv(
    "authors.csv",
    index=False,
    encoding="utf-8-sig"
)

# Guardar tabla autor-publicación en un archivo csv
df_autor_publicacion.to_csv(
    "author_publication.csv",
    index=False,
    encoding="utf-8-sig"
)


# Se construye una tabla que muestra la distribución de autores por publicacion
tabla_publicaciones = (
    df_autor_publicacion.groupby("EID")["Author_id"]
    .nunique()
    .reset_index(name="Total_autores")
    .sort_values("Total_autores", ascending=False)
    .reset_index(drop=True)
)
 
print("\nTabla de autores por publicación:")
print(tabla_publicaciones.head(20))


plt.figure()
plt.hist(tabla_publicaciones["Total_autores"].astype(float), bins=30)
plt.xlabel("N autores")
plt.ylabel("N publicaciones")
plt.title("Histograma productividad")
plt.show()


# El despliegue de esta tabla permite identificar la existencia de publicaciones científica con autoria masiva
# Estas publicaciones representan alrededor del 2% del total de publicaciones
# Una proporción enorme de tu red de autores existe únicamente por su participación en publicaciones de autoría masiva (41%)


# Se construye una tabla que expone la distribución de publicaciones por autor (Modo 1)
tabla_autores = (
    df_autor_publicacion.groupby("Author_id")["EID"]
    .nunique()
    .reset_index(name="Total_publicaciones")
    .sort_values("Total_publicaciones", ascending = False)
    .reset_index(drop=True)
    )

plt.figure()
plt.hist(tabla_autores["Total_publicaciones"].astype(float), bins=30)
plt.xlabel("N publicaciones")
plt.ylabel("N autores")
plt.title("Histograma productividad")
plt.show()

# Alrededor del 75% de los autores solo cuentan con una publicación científica

###############################################################################
# Se analizan algunos resultados
###############################################################################
caso = df_autor_publicacion[df_autor_publicacion["Author_id"]=="6602402405"]
caso = investiga[investiga["EID"]=="2-s2.0-84910080574"]




# Para corregir o tratar la presencia de las publicaciones con autoria masiva, debo utilizar un mecanismo de conteo fraccionado de productividad

"""
Conteo fraccionado de productividad por autor + histograma
-------------------------------------------------------------
Input esperado: df_autores con columnas EID, Year, Author_id
(formato largo: una fila por par autor-publicación)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------------------------------------------
# 1. Punto de partida: df_autores (EID, Year, Author_id)
# -----------------------------------------------------------------

# -----------------------------------------------------------------
# 2. Tamaño de equipo por publicación (número de autores por EID)
# -----------------------------------------------------------------
tamano_equipo = (
    df_autores.groupby("EID")["Author_id"]
    .nunique()
    .reset_index(name="Total_autores")
)

print("Publicaciones con autoría masiva (top 10):")
print(tamano_equipo.sort_values("Total_autores", ascending=False).head(10))

# -----------------------------------------------------------------
# 3. Crédito fraccionado por fila: 1 / Total_autores de esa publicación
# -----------------------------------------------------------------
df_autores_credito = df_autores.merge(tamano_equipo, on="EID", how="left")
df_autores_credito["credito_fraccionado"] = 1 / df_autores_credito["Total_autores"]

# Solo 20 publicaciones científicas cuentan con 1 autor durante el periodo de análisis


# -----------------------------------------------------------------
# 4. Productividad fraccionada por autor (suma de créditos a través de todas sus publicaciones)
# -----------------------------------------------------------------
productividad_fraccionada = (
    df_autores_credito.groupby("Author_id")["credito_fraccionado"]
    .sum()
    .reset_index(name="productividad_fraccionada")
    .sort_values("productividad_fraccionada", ascending=False)
    .reset_index(drop=True)
)

# -----------------------------------------------------------------
# 5. Comparación de referencia: productividad con conteo completo (para contraste)
# -----------------------------------------------------------------
productividad_completa = (
    df_autores.groupby("Author_id")["EID"]
    .nunique()
    .reset_index(name="productividad_completa")
)

comparacion = productividad_fraccionada.merge(productividad_completa, on="Author_id")

print("\nTabla de productividad fraccionada (top 15):")
print(comparacion.sort_values("productividad_fraccionada", ascending=False).head(15))

print("\nEstadísticos descriptivos -- conteo completo:")
print(comparacion["productividad_completa"].describe())

print("\nEstadísticos descriptivos -- conteo fraccionado:")
print(comparacion["productividad_fraccionada"].describe())

# Guardar tablas
comparacion.to_csv("/mnt/user-data/outputs/productividad_fraccionada_vs_completa.csv", index=False)

# -----------------------------------------------------------------
# 6. Histograma -- conteo COMPLETO (referencia, variable discreta)
# -----------------------------------------------------------------
plt.figure()
plt.hist(comparacion["productividad_completa"].astype(float), bins=30)
plt.xlabel("productividad_completa")
plt.ylabel("n autores")
plt.title("Histograma productividad completa")
plt.show()


# Histograma para la productividad fraccionada
plt.figure()
plt.hist(comparacion["productividad_fraccionada"].astype(float), bins=30)
plt.xlabel("productividad_fraccionada")
plt.ylabel("n autores")
plt.title("Histograma productividad fraccionada")
plt.show()

# versión que te sirve para tesis - con log
plt.figure()
plt.hist(comparacion["productividad_fraccionada"].astype(float), bins=30, log=True)
plt.xlabel("productividad_fraccionada")
plt.ylabel("Log (N de autores)")
plt.title("Histograma productividad fraccionada - escala log")
plt.show()


# Versión 1: conteo fraccionado (ya la tienes)
prop_baja_frac = (comparacion["productividad_fraccionada"] < 0.5).mean()

# Versión 2: excluyendo mega-papers (define un umbral, ej. 50+ autores)
umbral = 50
eids_excluir = tamano_equipo[tamano_equipo["Total_autores"] > umbral]["EID"]
df_sin_mega = df_autores[~df_autores["EID"].isin(eids_excluir)]

productividad_sin_mega = (
    df_sin_mega.groupby("Author_id")["EID"]
    .nunique()
    .reset_index(name="Total_publicaciones")
)
prop_baja_exclusion = (productividad_sin_mega["Total_publicaciones"] == 1).mean()


# Criterio equivalente: productividad == 1 en AMBAS versiones (sin fraccionar todavía)
prop_1pub_original = (productividad_completa["productividad_completa"] == 1).mean()
prop_1pub_sin_mega = (productividad_sin_mega["Total_publicaciones"] == 1).mean()

print(f"Proporción con 1 publicación -- dataset ORIGINAL completo: {prop_1pub_original:.2%}")
print(f"Proporción con 1 publicación -- tras EXCLUSIÓN de mega-papers: {prop_1pub_sin_mega:.2%}")


# Se elabora una covariante nodal asociada con la productividad científica completa
# df_autor_credito tiene Author_id, Year, credito_fraccionado
# Productividad del año t - para POOLED sin lag
df_dinamico = (
    df_autores_credito.groupby(["Author_id","Year"])["credito_fraccionado"].sum()
   .reindex(pd.MultiIndex.from_product(
        [df_nodos['Author_id'], range(2010,2025)],
        names=['id_nodo','anio']), fill_value=0)
   .unstack(level=1, fill_value=0)
   .reset_index()
)

# Ver 2010 con valores > 0
df_dinamico[df_dinamico[2010] > 0][['id_nodo', 2010]].head(10)

# Guardar tabla de covariante nodal asociada con la producción científica con rezago considerando el periodo 2013 - 2024
df_dinamico.to_csv(
    "produccion_cientifica.csv",
    index=False,
    encoding="utf-8-sig"
)




# Se utiliza un dataframe preestablecido con información de autores y sus afiliaciones a nivel temporal
scopus = pd.read_csv("tbl_ws_api_scopus_detalle_afiliacion_publicaciones_renacyt.csv",encoding='utf-8', delimiter = ",")
scopus["auth_id"] = scopus["auth_id"].apply(lambda x: str(x))

# Se utiliza un dataframe que contiene una extensión de atributos de las publicaciones científicas
pub_scopus = pd.read_excel("tbl_publicaciones_scopus.xlsx", sheet_name="tbl_scopus_pub", header=0)
pub_scopus.columns
pub_scopus = pub_scopus[["eid", "cover_date"]]

# Solo se considera el año de la publicación
pub_scopus["cover_date"] = pd.to_datetime(pub_scopus["cover_date"], errors='coerce')
pub_scopus["year"] = pub_scopus["cover_date"].dt.year

del pub_scopus["cover_date"]

# Se realiza una fusion entre scopus y pub_scopus
fusion = pd.merge(scopus, pub_scopus, on="eid", how="left")

# Del dataframe fusion, se consideran solo las publicaciones listadas en una reducción del dataframe investiga
investiga1 = investiga[["EID"]]
# Se renombra el atributo EID del dataframe investiga1
investiga1.rename(columns=({"EID":"eid"}), inplace=True)
fusion2 = pd.merge(fusion, investiga1, on="eid", how="right")
fusion2["eid"].nunique()
fusion2["auth_id"] = fusion2["auth_id"].apply(lambda x: str(x))
fusion2.columns


# Considerando fusion2 se crea un dataframe con solo autores y sus afiliaciones
fusion3 = fusion2[["auth_id", "auth_name", "affil_name", "affiliation_country"]]
fusion3 = fusion3.drop_duplicates(subset=["auth_name"])
                        

# Se carga un archivo compartido por R
def int_to_str(value):
    return str(value)

# Especifica el diccionario de conversión en el parámetro converters
converters = {"Author_id": int_to_str}

investigador_r = pd.read_excel("autores_recurrentes_gwb1dsp.xlsx", sheet_name="Autores_Recurrentes_IDs", header=0, converters=converters)
investigador_r.rename(columns=({"Author_id":"auth_id"}), inplace=True)

# Se fusion f4
f4 = pd.merge(investigador_r, fusion3, on="auth_id", how="left")












