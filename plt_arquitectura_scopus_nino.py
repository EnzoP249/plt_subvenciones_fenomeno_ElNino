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

# Se carga el archivo que contiene información de scopus de publicaciones científicas en torno al fenómeno El Niñó en donde al
# al menos un investigador consignó como afiliación a una entidad peruana en formato csv y
# se convierte en un objeto dataframe

investiga = pd.read_csv("scopus_export_Jul 20-2026_ced6233f-1ae9-4552-96e3-f7b043495d28.csv", engine="python", encoding="latin1", sep=",")

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
investiga = investiga[["EID", "DOI", "Title", "Year", "Cited by", "Document_type", "Publisher", "Author full names", "Authors with affiliations"]]

# Se realiza por segunda vez una análisis del dataframe investiga con las variaciones hechas
investiga.shape
investiga.columns
investiga.dtypes
investiga.info()

# Se analiza la distribución de las publicaciones científicas (2014 - 2024) considerando el tipo de documento, desde una dimensión absoluta y proporcional
investiga.Document_type.value_counts()
(investiga["Document_type"]
 .value_counts(normalize=True)
 .mul(100)
 .round(1))


# Se analiza la distribución de las publicaciones científicas (2014 - 2024) considerando el publisher, desde una dimensión absoluta y proporcional
investiga.Publisher.value_counts()
(investiga["Publisher"]
 .value_counts(normalize=True)
 .mul(100)
 .round(1))


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
















# Se gráfica la distribución de las publicaciones científicas por año
investiga_año = investiga_año.sort_values("Year")

# Colores institucionales
color_principal = "#00A7B5"   # turquesa
color_secundario = "#5FB7C6"  # azul petróleo

# Tamaño más amplio (clave para separar barras)
plt.figure(figsize=(12,6))

# Crear barras con menor ancho (más espacio)
bars = plt.bar(observa_año["AÑO"], observa_año["ID_CONTRATO"], 
               color=color_principal, 
               width=0.6)

# Etiquetas
plt.xlabel("Año", fontsize=11, color="black")
plt.ylabel("Número de subvenciones", fontsize=11, color="black")

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

años = observa_año["AÑO"].dropna().astype(int).tolist()
ax.set_xticks(años)
ax.set_xticklabels([str(a) for a in años], rotation=0)

# Etiquetas
for x, y in zip(observa_año["AÑO"], observa_año["ID_CONTRATO"]):
    #if pd.notna(x) and pd.notna(y) and y > 100:
        plt.text(
            float(x),
            float(y)+5,
            f"{int(y)}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=color_secundario
        )

# Margen superior para que no choque texto
plt.ylim(0, observa_año["ID_CONTRATO"].max() * 1.15)

plt.tight_layout()
plt.show()









