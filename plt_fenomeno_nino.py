# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 22:14:23 2026

@author: Enzo
"""

###############################################################################
# El proyecto sigue un enfoque de librerias integradas
###############################################################################

# Se importan las librerias que serán usadas
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import FuncFormatter
import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF



###############################################################################
# Se describen los colores que integran la paleta institucional para mis gráficos
###############################################################################

#1. Celeste claro
#HEX: #5FB7C6
#Nombre descriptivo: Celeste muy claro
#Uso: fondos, áreas suaves, mapas base

#2. Verde olivo
#HEX: #A3AD2C
#Nombre descriptivo: Verde olivo institucional
#Uso: color principal de datos (barras, líneas)

#3. Azul petróleo
#HEX: #0B4F6C
#Nombre descriptivo: Azul petróleo
#Uso: énfasis, títulos, bordes

# Se carga el archivo xlsx y se convierte en un objeto dataframe
observa = pd.read_excel("bd_subvenciones_nino.xlsx", sheet_name="Resultados", header=0)

# Se analiza la estructura del dataframe observa
observa.shape
observa.columns
observa.info()
observa.dtypes
observa.head(10)

# Se renombran variables del dataframe observa
observa.rename(columns=({"N° CONTRATO":"ID_CONTRATO",
                         "LÍDER DEL PROYECTO":"LIDER_PROYECTO",
                         "MONTO (S/)":"MONTO",
                         "PUB.":"PUB",
                         "PAT.":"PAT"}), inplace=True)



# Se identifica la presencia de duplicados en el dataframe observa
duplicado = observa.duplicated(subset=["ID_CONTRATO"])
print("¿Existe la presencia de duplicados?:", duplicado.any())


# Se identifica la presencia de nulos en el dataframe observa
nulo = observa["ID_CONTRATO"].isna().sum()
print(f"la columna ID_CONTRATO contiene {nulo} valores nulos")

# se realiza una distribución de cantidad de subvenciones por año
observa_año = observa.groupby("AÑO")["ID_CONTRATO"].count()
observa_año = observa_año.to_frame()
observa_año.reset_index(inplace=True)

# Se analiza los tipos de datos de las columnas que conforman el dataframe observa_año
observa_año.info()

# Se cambian los atributos a tipo númerico
observa_año["AÑO"] = pd.to_numeric(observa_año["AÑO"], errors="coerce")
observa_año["ID_CONTRATO"] = pd.to_numeric(observa_año["ID_CONTRATO"], errors="coerce")

# Se calcula la cantidad de subvenciones durante el periodo de análisis
observa["ID_CONTRATO"].count()

# Se calcula la suma del total de subvenciones durante el periodo de análisis
observa["MONTO"].sum()


###############################################################################
# Se realiza una gráfico de barras considerando el dataframe df_biotech_año que
# muestra la relación entre el número de subvenciones otorgadas y el monto financiado
###############################################################################

df_nino_año = (observa.groupby("AÑO", as_index=False).agg({"MONTO":"sum", "ID_CONTRATO":"count"}))
# Se renombra la columna ID_CONTRATO del dataframe df_biotech_año
df_nino_año.rename(columns=({"ID_CONTRATO":"CANTIDAD"}), inplace=True)


df_plot = df_nino_año.copy()

df_plot["AÑO"] = pd.to_numeric(df_plot["AÑO"], errors="coerce")
df_plot["MONTO"] = pd.to_numeric(df_plot["MONTO"], errors="coerce")
df_plot["CANTIDAD"] = pd.to_numeric(df_plot["CANTIDAD"], errors="coerce")

df_plot = df_plot.dropna(subset=["AÑO", "MONTO", "CANTIDAD"]).copy()
df_plot["AÑO"] = df_plot["AÑO"].astype(int)

df_plot = df_plot.sort_values("AÑO")

# ----------------------------
# Colores institucionales
# ----------------------------
color_monto = "#5FB7C6"   # celeste institucional
color_prod = "#0B4F6C"    # azul petróleo

fig, ax1 = plt.subplots(figsize=(14, 7))

color_monto = "#5FB7C6"
color_prod = "#0B4F6C"

bars = ax1.bar(
    df_plot["AÑO"],
    df_plot["MONTO"],
    color=color_monto,
    alpha=0.85,
    width=0.6,
    edgecolor="white",
    linewidth=1
)

ax1.set_xlabel("Año", fontsize=11)
ax1.set_ylabel("Monto (Millones de S/)", fontsize=11, color=color_monto)
ax1.tick_params(axis="y", labelcolor=color_monto)

años = df_plot["AÑO"].astype(int).tolist()
ax1.set_xticks(años)
ax1.set_xticklabels(años)

ax2 = ax1.twinx()

ax2.plot(
    df_plot["AÑO"],
    df_plot["CANTIDAD"],
    color=color_prod,
    marker="o",
    linewidth=2.6,
    markersize=6,
    zorder=5
)

ax2.set_ylabel("N.° de subvenciones", fontsize=11, color=color_prod)
ax2.tick_params(axis="y", labelcolor=color_prod)

# ----------------------------
# Etiquetas de barras: dentro si son altas, fuera si son bajas
# ----------------------------
max_monto = df_plot["MONTO"].max()

for bar in bars:
    height = bar.get_height()
    x = bar.get_x() + bar.get_width() / 2
    label = f"{height / 1e6:.1f}M"

    if height > max_monto * 0.18:
        y_text = height - max_monto * 0.045
        va = "top"
        color_label = "white"
    else:
        y_text = height + max_monto * 0.018
        va = "bottom"
        color_label = color_monto

    ax1.text(
        x,
        y_text,
        label,
        ha="center",
        va=va,
        fontsize=8.5,
        color=color_label,
        fontweight="bold"
    )

# ----------------------------
# Etiquetas de línea: caja sutil y alternancia
# ----------------------------
max_line = df_plot["CANTIDAD"].max()

bbox_line = dict(
    boxstyle="round,pad=0.18",
    facecolor="white",
    edgecolor="none",
    alpha=0.80
)

for i, (x, y) in enumerate(zip(df_plot["AÑO"], df_plot["CANTIDAD"])):

    if i % 2 == 0:
        offset = max_line * 0.055
        va = "bottom"
    else:
        offset = -max_line * 0.065
        va = "top"

    ax2.text(
        x,
        y + offset,
        f"{int(y)}",
        ha="center",
        va=va,
        fontsize=9,
        color=color_prod,
        fontweight="bold",
        bbox=bbox_line,
        zorder=6
    )

# ----------------------------
# Estética
# ----------------------------
ax1.spines["top"].set_visible(False)
ax2.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)

ax1.grid(axis="y", linestyle="--", alpha=0.22)
ax1.set_axisbelow(True)

ax1.set_ylim(0, max_monto * 1.15)
ax2.set_ylim(0, max_line * 1.18)

plt.tight_layout()
plt.show()




import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ------------------------------------------------
# Preparación de los datos
# ------------------------------------------------
df_plot = df_plot.sort_values("AÑO").copy()

df_plot["AÑO"] = df_plot["AÑO"].astype(int)
df_plot["MONTO_MILLONES"] = df_plot["MONTO"] / 1_000_000

# ------------------------------------------------
# Colores institucionales
# ------------------------------------------------
color_monto = "#5FB7C6"   # celeste institucional
color_linea = "#0B4F6C"   # azul petróleo
color_texto = "#333333"
color_grilla = "#D9D9D9"

# ------------------------------------------------
# Creación del gráfico
# ------------------------------------------------
fig, ax1 = plt.subplots(figsize=(15, 7.5))

bars = ax1.bar(
    df_plot["AÑO"],
    df_plot["MONTO_MILLONES"],
    width=0.58,
    color=color_monto,
    edgecolor="none",
    zorder=2
)

# ------------------------------------------------
# Eje izquierdo: financiamiento
# ------------------------------------------------
ax1.set_xlabel(
    "Año",
    fontsize=11,
    color=color_texto,
    labelpad=10
)

ax1.set_ylabel(
    "Financiamiento adjudicado (millones de S/)",
    fontsize=11,
    color=color_monto,
    labelpad=12
)

ax1.tick_params(
    axis="y",
    labelcolor=color_monto,
    colors=color_monto,
    length=0
)

ax1.tick_params(
    axis="x",
    colors=color_texto,
    length=0,
    pad=8
)

ax1.set_xticks(df_plot["AÑO"])
ax1.set_xticklabels(df_plot["AÑO"])

ax1.yaxis.set_major_formatter(
    mticker.StrMethodFormatter("{x:,.0f}")
)

# ------------------------------------------------
# Etiquetas de financiamiento dentro de las barras
# ------------------------------------------------
max_monto = df_plot["MONTO_MILLONES"].max()

for bar, año, monto in zip(
    bars,
    df_plot["AÑO"],
    df_plot["MONTO_MILLONES"]
):
    x = bar.get_x() + bar.get_width() / 2
    height = bar.get_height()

    # Posición general dentro de la columna
    posicion_relativa = 0.72

    # En estos años la línea atraviesa la parte superior de la barra.
    # Por ello, el monto se coloca más abajo.
    if año in [2016, 2017]:
        posicion_relativa = 0.48

    # Para las barras muy altas, la etiqueta queda cerca de la parte superior
    if height >= max_monto * 0.55:
        posicion_relativa = 0.88

    y = height * posicion_relativa

    ax1.text(
        x,
        y,
        f"{monto:.1f}M",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="white",
        zorder=4
    )

# ------------------------------------------------
# Eje derecho: número de subvenciones
# ------------------------------------------------
ax2 = ax1.twinx()

ax2.plot(
    df_plot["AÑO"],
    df_plot["CANTIDAD"],
    color=color_linea,
    linewidth=2.4,
    marker="o",
    markersize=6.5,
    markerfacecolor="white",
    markeredgecolor=color_linea,
    markeredgewidth=2,
    zorder=5
)

ax2.set_ylabel(
    "Número de subvenciones",
    fontsize=11,
    color=color_linea,
    labelpad=12
)

ax2.tick_params(
    axis="y",
    labelcolor=color_linea,
    colors=color_linea,
    length=0
)

ax2.yaxis.set_major_locator(
    mticker.MaxNLocator(integer=True)
)

# ------------------------------------------------
# Etiquetas del número de subvenciones
# ------------------------------------------------

# Ajustes particulares para evitar cruces con barras y segmentos de línea
offsets_linea = {
    2013: (0, 11),
    2014: (0, 11),
    2015: (0, 11),

    # Situaciones problemáticas
    2016: (0, 13),
    2017: (0, 13),

    2018: (0, -18),
    2019: (0, 13),
    2020: (0, -18),
    2021: (0, 13),
    2022: (0, -18),
    2023: (0, 13),
    2024: (0, -18),
    2025: (0, 13),
    2026: (0, 13)
}

for año, cantidad in zip(
    df_plot["AÑO"],
    df_plot["CANTIDAD"]
):
    desplazamiento = offsets_linea.get(año, (0, 11))

    ax2.annotate(
        f"{int(cantidad)}",
        xy=(año, cantidad),
        xytext=desplazamiento,
        textcoords="offset points",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=color_linea,
        bbox=dict(
            boxstyle="round,pad=0.16",
            facecolor="white",
            edgecolor="none",
            alpha=0.92
        ),
        zorder=7,
        annotation_clip=False
    )

# ------------------------------------------------
# Límites de los ejes
# ------------------------------------------------
ax1.set_ylim(
    0,
    max_monto * 1.16
)

ax2.set_ylim(
    0,
    df_plot["CANTIDAD"].max() * 1.18
)


# ------------------------------------------------
# Leyenda conjunta
# ------------------------------------------------
barra_leyenda = plt.Rectangle(
    (0, 0),
    1,
    1,
    color=color_monto
)

linea_leyenda = plt.Line2D(
    [0],
    [0],
    color=color_linea,
    linewidth=2.4,
    marker="o",
    markerfacecolor="white",
    markeredgewidth=2
)

ax1.legend(
    [barra_leyenda, linea_leyenda],
    ["Financiamiento", "Número de subvenciones"],
    loc="upper left",
    frameon=False,
    ncol=2,
    fontsize=9
)

# ------------------------------------------------
# Estética general
# ------------------------------------------------
ax1.grid(
    axis="y",
    linestyle="--",
    linewidth=0.8,
    color=color_grilla,
    alpha=0.60,
    zorder=0
)

ax1.set_axisbelow(True)

ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.spines["left"].set_visible(False)

ax2.spines["top"].set_visible(False)
ax2.spines["left"].set_visible(False)

ax1.spines["bottom"].set_color("#BFBFBF")
ax2.spines["right"].set_color("#BFBFBF")

fig.subplots_adjust(
    top=0.84,
    bottom=0.12,
    left=0.08,
    right=0.92
)

plt.show()


###############################################################################
# Se realiza una gráfico de barras agrupadas considerando el dataframe obv_año_estado
# para analizar a las subvenciones concluidas y activas
###############################################################################

# se realiza una distribución de cantidad de subvenciones por año y por estado
obv_año_estado = pd.pivot_table(observa, values="ID_CONTRATO", index="AÑO", columns="ESTADO", aggfunc="count")
obv_año_estado.reset_index(inplace=True)


obv_año_estado["Activo"] = pd.to_numeric(obv_año_estado["Activo"], errors="coerce")
obv_año_estado["Concluido"] = pd.to_numeric(obv_año_estado["Concluido"], errors="coerce")

# Reemplazar nulos por 0 (decisión lógica en este caso)
obv_año_estado["Activo"] = obv_año_estado["Activo"].fillna(0)
obv_año_estado["Concluido"] = obv_año_estado["Concluido"].fillna(0)

obv_año_estado["AÑO"] = pd.to_numeric(obv_año_estado["AÑO"], errors="coerce").astype(int)

obv_año_estado = obv_año_estado.sort_values("AÑO")

# Posiciones
x = np.arange(len(obv_año_estado))
width = 0.35

# Colores institucionales
color_activo = "#A3AD2C"     
color_concluido = "#1F6F8B"  # azul petróleo

fig, ax = plt.subplots(figsize=(12, 6))

# Barras
bars1 = ax.bar(x - width/2, obv_año_estado["Activo"], width, label="Activo", color=color_activo)
bars2 = ax.bar(x + width/2, obv_año_estado["Concluido"], width, label="Concluido", color=color_concluido)

# Ejes
ax.set_xlabel("Año", fontsize=11)
ax.set_ylabel("Número de subvenciones", fontsize=11)
#ax.set_title("Contratos por estado y año", fontsize=14, pad=15)

# Eje X con todos los años
ax.set_xticks(x)
ax.set_xticklabels(obv_año_estado["AÑO"].astype(int))

# Estética consultoría
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.set_axisbelow(True)

# Leyenda limpia
ax.legend(frameon=False)

# Etiquetas encima de barras
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width()/2,
                height + max(obv_año_estado[["Activo","Concluido"]].max()) * 0.01,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=12
            )

# Margen superior
ax.set_ylim(0, obv_año_estado[["Activo","Concluido"]].max().max() * 1.15)

plt.tight_layout()
plt.show()

###############################################################################
# Se realiza un gráfico de barras para observar la distribución de las subvenciones
# vinculadas al fenómeno el niño, según intervención
###############################################################################
total = observa["INTERVENCIÓN"].value_counts()

proporcion = (
    observa["INTERVENCIÓN"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

nino_intervencion = pd.DataFrame({
    "TOTAL": total,
    "PROPORCION (%)": proporcion
})


nino_intervencion
nino_intervencion.reset_index(inplace=True)
nino_intervencion.columns

nino_intervencion = nino_intervencion.sort_values("TOTAL", ascending=True)

color_principal = "#0B4F6C"   # azul institucional
color_secundario = "#5FB7C6"  # celeste

plt.figure(figsize=(12, 6))

bars = plt.barh(
    nino_intervencion["INTERVENCIÓN"],
    nino_intervencion["PROPORCION (%)"],
    color=color_principal
)

# Etiquetas: porcentaje + total
for i, (pct, total) in enumerate(
    zip(
        nino_intervencion["PROPORCION (%)"],
        nino_intervencion["TOTAL"]
    )
):
    plt.text(
        pct + 3,
        i,
        f"{pct:.1f}% ({total:,})",
        va="center",
        fontsize=14
    )

plt.xlabel("Participación (%)")

plt.gca().spines["top"].set_visible(False)
plt.gca().spines["right"].set_visible(False)

plt.grid(axis="x", linestyle="--", alpha=0.3)

plt.tight_layout()
plt.show()


###############################################################################
# Considerando el dataframe observa, se elabora un gráfico de tablas apiladas
# para describir el número de subvenciones en su condición de activo y concluido
# por intervención
###############################################################################

df_resumen = (
    observa.groupby(["INTERVENCIÓN", "ESTADO"])
      .size()
      .unstack(fill_value=0)
      .reset_index()
)

df_resumen

# Se organiza en función de Concluido
df_resumen = df_resumen.sort_values("Concluido", ascending=True)

# ==============================================
# Preparación
# ==============================================
df_resumen = df_resumen.copy()

df_resumen["TOTAL"] = (
    df_resumen["Activo"] +
    df_resumen["Concluido"]
)

# Ordenar de mayor a menor
df_resumen = df_resumen.sort_values(
    "TOTAL",
    ascending=True
)

# ==============================================
# Colores institucionales
# ==============================================
color_activo = "#5FB7C6"
color_concluido = "#0B4F6C"

fig, ax = plt.subplots(figsize=(12, 6))

# ==============================================
# Barras horizontales apiladas
# ==============================================
bars_activo = ax.barh(
    df_resumen["INTERVENCIÓN"],
    df_resumen["Activo"],
    color=color_activo,
    height=0.62,
    label="Activo"
)

bars_concluido = ax.barh(
    df_resumen["INTERVENCIÓN"],
    df_resumen["Concluido"],
    left=df_resumen["Activo"],
    color=color_concluido,
    height=0.62,
    label="Concluido"
)

# ==============================================
# Etiquetas internas: Activo
# ==============================================
for bar, valor in zip(
    bars_activo,
    df_resumen["Activo"]
):
    if valor > 0:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() / 2,
            f"{int(valor)}",
            ha="center",
            va="center",
            color="white",
            fontsize=11,
            fontweight="bold"
        )

# ==============================================
# Etiquetas internas: Concluido
# ==============================================
for bar, valor in zip(
    bars_concluido,
    df_resumen["Concluido"]
):
    if valor > 0:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_y() + bar.get_height() / 2,
            f"{int(valor)}",
            ha="center",
            va="center",
            color="white",
            fontsize=11,
            fontweight="bold"
        )

# ==============================================
# Total al final de cada barra
# ==============================================
for bar, total in zip(
    bars_concluido,
    df_resumen["TOTAL"]
):
    ax.text(
        total + 1,
        bar.get_y() + bar.get_height() / 2,
        f"{int(total)}",
        ha="left",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="#5B2C6F"
    )

# ==============================================
# Estética
# ==============================================
ax.set_xlabel(
    "Número de subvenciones",
    fontsize=11
)

ax.set_ylabel("")

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 1.08),
    ncol=2,
    frameon=False
)

ax.grid(
    axis="x",
    linestyle="--",
    alpha=0.22
)

ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

ax.tick_params(
    axis="y",
    length=0
)

ax.set_xlim(
    0,
    df_resumen["TOTAL"].max() * 1.12
)

plt.tight_layout()
plt.show()


###############################################################################
# Se realiza un gráfico para identificar quienes investigan en nino en el Perú
# por investigador y por universidad e IPI
################################################################################

total = observa["LIDER_PROYECTO"].value_counts()

proporcion = (
    observa["LIDER_PROYECTO"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

nino_proyecto = pd.DataFrame({
    "TOTAL": total,
    "PROPORCION (%)": proporcion
})


nino_proyecto
nino_proyecto.reset_index(inplace=True)
nino_proyecto = nino_proyecto.head(10)
nino_intervencion.columns

nino_proyecto = nino_proyecto.sort_values("TOTAL", ascending=True)

color_principal = "#5FB7C6"   # azul institucional
color_secundario = "#0B4F6C"  # celeste

plt.figure(figsize=(12, 6))

bars = plt.barh(
    nino_proyecto["LIDER_PROYECTO"],
    nino_proyecto["PROPORCION (%)"],
    color=color_principal
)

# Etiquetas: porcentaje + total
for i, (pct, total) in enumerate(
    zip(
        nino_proyecto["PROPORCION (%)"],
        nino_proyecto["TOTAL"]
    )
):
    plt.text(
        pct + 0.2,
        i,
        f"{pct:.1f}% ({total:,})",
        va="center",
        fontsize=16
    )

plt.xlabel("Participación")

plt.gca().spines["top"].set_visible(False)
plt.gca().spines["right"].set_visible(False)

plt.grid(axis="x", linestyle="--", alpha=0.3)

plt.tight_layout()
plt.show()

# Considerando el dataframe observa, se crea un dataframe que contenga solo a universidades e IPI
ipi_nino = observa[observa["ENTIDAD_SINACTI"]=="IPI"]

total = ipi_nino["ORGANIZACIÓN"].value_counts()

proporcion = (
    ipi_nino["ORGANIZACIÓN"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

ipi_nino_proyecto = pd.DataFrame({
    "TOTAL": total,
    "PROPORCION (%)": proporcion
})


ipi_nino_proyecto
ipi_nino_proyecto.reset_index(inplace=True)
#ipi_nino_proyecto = nino_proyecto.head(10)
ipi_nino_proyecto.columns

ipi_nino_proyecto = ipi_nino_proyecto.sort_values("TOTAL", ascending=True)

color_principal = "#5FB7C6"   # azul institucional
color_secundario = "#0B4F6C"  # celeste

plt.figure(figsize=(12, 6))

bars = plt.barh(
    ipi_nino_proyecto["ORGANIZACIÓN"],
    ipi_nino_proyecto["PROPORCION (%)"],
    color=color_principal
)

# Etiquetas: porcentaje + total
for i, (pct, total) in enumerate(
    zip(
        ipi_nino_proyecto["PROPORCION (%)"],
        ipi_nino_proyecto["TOTAL"]
    )
):
    plt.text(
        pct + 0.2,
        i,
        f"{pct:.1f}% ({total:,})",
        va="center",
        fontsize=16
    )

plt.xlabel("Participación")

plt.gca().spines["top"].set_visible(False)
plt.gca().spines["right"].set_visible(False)

plt.grid(axis="x", linestyle="--", alpha=0.3)

plt.tight_layout()
plt.show()

###############################################################################
###############################################################################

ipi_nino = observa[observa["ENTIDAD_SINACTI"]=="UNIVERSIDAD"]

total = ipi_nino["ORGANIZACIÓN"].value_counts()

proporcion = (
    ipi_nino["ORGANIZACIÓN"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

ipi_nino_proyecto = pd.DataFrame({
    "TOTAL": total,
    "PROPORCION (%)": proporcion
})


ipi_nino_proyecto
ipi_nino_proyecto.reset_index(inplace=True)
ipi_nino_proyecto = ipi_nino_proyecto.head(10)
ipi_nino_proyecto.columns

ipi_nino_proyecto = ipi_nino_proyecto.sort_values("TOTAL", ascending=True)

color_principal = "#5FB7C6"   # azul institucional
color_secundario = "#0B4F6C"  # celeste

plt.figure(figsize=(12, 6))

bars = plt.barh(
    ipi_nino_proyecto["ORGANIZACIÓN"],
    ipi_nino_proyecto["PROPORCION (%)"],
    color=color_principal
)

# Etiquetas: porcentaje + total
for i, (pct, total) in enumerate(
    zip(
        ipi_nino_proyecto["PROPORCION (%)"],
        ipi_nino_proyecto["TOTAL"]
    )
):
    plt.text(
        pct + 0.2,
        i,
        f"{pct:.1f}% ({total:,})",
        va="center",
        fontsize=16
    )

plt.xlabel("Participación")

plt.gca().spines["top"].set_visible(False)
plt.gca().spines["right"].set_visible(False)

plt.grid(axis="x", linestyle="--", alpha=0.3)

plt.tight_layout()
plt.show()


###############################################################################
# Se analiza la relación entre el financiamiento y la producción científica
# en las universidades
universidad_nino = observa[observa["ENTIDAD_SINACTI"]=="UNIVERSIDAD"]
universidad_nino.columns

# me quedo solo con los contratos en condición de concluido
universidad_nino = universidad_nino[universidad_nino["ESTADO"]=="Concluido"]
universidad_nino["PRODUCCION"] = universidad_nino["PUB"] + universidad_nino["TESIS"] + universidad_nino["PAT"]
universidad_nino = universidad_nino[universidad_nino["PRODUCCION"]!= 0]


observa_uni_pre = (universidad_nino.groupby("ORGANIZACIÓN", as_index=False).agg({"MONTO":"sum", "PRODUCCION":"sum"}))

df_plot = observa_uni_pre.copy()

# Conversión de tipos
df_plot["MONTO"] = pd.to_numeric(df_plot["MONTO"], errors="coerce")
df_plot["PRODUCCION"] = pd.to_numeric(df_plot["PRODUCCION"], errors="coerce")

# Limpieza
df_plot = df_plot.dropna(subset=["MONTO", "PRODUCCION"]).copy()

# Escala en millones
df_plot["MONTO_M"] = df_plot["MONTO"] / 1e6

# =========================================================
# 3. ABREVIACIÓN DE INSTITUCIONES
# =========================================================
map_dict = {
    "PONTIFICIA UNIVERSIDAD CATOLICA DEL PERU": "PUCP",
    "UNIVERSIDAD ANDINA DEL CUSCO": "UAC",
    "UNIVERSIDAD CATOLICA DE SANTA MARIA": "UCSM",
    "UNIVERSIDAD CATOLICA SAN PABLO": "UCSP",
    "UNIVERSIDAD ANTONIO RUIZ DE MONTOYA": "UARM",
    "UNIVERSIDAD CATOLICA LOS ANGELES DE CHIMBOTE": "ULADECH",
    "ASOCIACION CIVIL UNIVERSIDAD DE CIENCIAS Y HUMANIDADES UCH": "UCH",
    "UNIVERSIDAD PERUANA CAYETANO HEREDIA": "UPCH",
    "UNIVERSIDAD NACIONAL DE INGENIERIA UNI":"UNI",
    "UNIVERSIDAD NACIONAL AGRARIA LA MOLINA":"UNALM",
    "UNIVERSIDAD NACIONAL MAYOR DE SAN MARCOS":"UNMSM",
    "UNIVERSIDAD NACIONAL TORIBIO RODRIGUEZ DE MENDOZA DE AMAZONAS":"UNTRM",
    "UNIVERSIDAD DE INGENIERIA Y TECNOLOGIA":"UTEC",
    "UNIVERSIDAD NACIONAL DE SAN AGUSTIN":"UNSA",
    "UNIVERSIDAD DE PIURA":"UDEP",
    "UNIVERSIDAD NACIONAL DE TRUJILLO":"UNT",
    "UNIVERSIDAD DE SAN MARTIN DE PORRES":"USMP",
    "UNIVERSIDAD PERUANA DE CIENCIAS APLICADAS S.A.C.":"UPC",
    "UNIVERSIDAD CIENTIFICA DEL SUR S.A.C.":"UCSUR",
    "UNIVERSIDAD NACIONAL DE SAN MARTIN":"UNSM",
    "UNIVERSIDAD NACIONAL DEL CENTRO DEL PERU":"UNCP",
    "UNIVERSIDAD NACIONAL DEL ALTIPLANO PUNO":"UNA",
    "UNIVERSIDAD PRIVADA ANTENOR ORREGO":"UPAO",
    "UNIVERSIDAD NACIONAL DE TUMBES":"UNTumbes",
    "UNIVERSIDAD CIENTIFICA DEL PERU":"UCP",
    "UNIVERSIDAD NACIONAL DE CAJAMARCA":"UNC",
    "UNIVERSIDAD NACIONAL DEL SANTA":"UNS",
    "UNIVERSIDAD CONTINENTAL SOCIEDAD ANONIMA CERRADA":"UCon",
    "UNIVERSIDAD NACIONAL DE JAÉN":"UJaén"
}

df_plot["ORG_SHORT"] = df_plot["ORGANIZACIÓN"].map(map_dict)

# Si alguna no está en el diccionario, usar nombre original corto
df_plot["ORG_SHORT"] = df_plot["ORG_SHORT"].fillna(
    df_plot["ORGANIZACIÓN"].str[:15]
)

# =========================================================
# 4. CÁLCULO DE TENDENCIA
# =========================================================
x = df_plot["MONTO_M"]
y = df_plot["PRODUCCION"]

coef = np.polyfit(x, y, 1)
trend = np.poly1d(coef)

# =========================================================
# 5. GRÁFICO
# =========================================================
fig, ax = plt.subplots(figsize=(10, 6))

# Scatter
ax.scatter(
    x,
    y,
    color="#5FB7C6",
    s=90,
    edgecolors="white",
    linewidth=1.5
)

# Línea de tendencia
#ax.plot(
    #x,
    #trend(x),
    #color="#0B4F6C",
    #linewidth=2.2)

# =========================================================
# 6. ETIQUETAS INTELIGENTES
# =========================================================
for _, row in df_plot.iterrows():
    
    # Mostrar solo instituciones relevantes (evita saturación)
    if row["PRODUCCION"] >= 9 or row["MONTO_M"]>=1.25:
        
        ax.text(
            row["MONTO_M"],
            row["PRODUCCION"],
            row["ORG_SHORT"],
            fontsize=9,
            ha="left",
            va="center",
            color="#0B4F6C",
            fontweight="bold"
        )

# =========================================================
# 7. ESTÉTICA
# =========================================================
#ax.set_title(
   # "Relación entre financiamiento y producción científica por institución",
    #fontsize=14,
    #color="#0B4F6C",
    #pad=15
#)

ax.set_xlabel("Monto (millones de S/)")
ax.set_ylabel("Producción científica")

ax.grid(alpha=0.25)

ax.set_xlim(0, df_plot["MONTO_M"].quantile(0.99) * 1.1)
ax.set_ylim(0, df_plot["PRODUCCION"].quantile(0.99) * 1.1)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.show()

###############################################################################
# Se elabora un listado con las subvenciones orientadas especificamente a investigación
# científica en su condición de activo y concluido
###############################################################################

investiga = observa[observa["INTERVENCIÓN"]=="INVESTIGACIÓN CIENTÍFICA"]

# divido investiga en dos dataframes
investiga_concluido = investiga[investiga["ESTADO"]=="Concluido"]
investiga_activo = investiga[investiga["ESTADO"]=="Activo"]

# Considerando el dataframe investiga_concluido, elimina aquellos proyectos que no hayan decantado en
# publicaciones científicas
investiga_concluido_pub = investiga_concluido[investiga_concluido["PUB"]>0]

# El dataframe investiga_concluido se convierte en un archivo excel para un análisis más detallado de cada publicación
investiga_concluido.to_excel("proyectos_publicaciones_concluidos_niño.xlsx")


# Considerando el dataframe investiga_concluido, elimino algunos proyectos que no se encuentran asociados
# explícitamente con el Fenómeno El Niño

contratos_eliminar = [
    "164-2016",
    "163-2018-FONDECYT-BM-IADT-SE",
    "J014-2016",
    "007-2019",
    "CONV-000008-2013-FONDECYT-DE (1)",
    "010-2019-FONDECYT-BM",
    "036-2021",
    "116-2016",
    "412-2019",
    "415-2019",
    "J107-2016",
    "060-2021",
    "124-2018",
    "027-2019-FONDECYT-BM",
    "PE501082856-2023",
    "015-2017",
    "059-2021",
    "CONT-000010-2013-FONDECYT-DE",
    "030-2021",
    "PE501082076-2023"
]

investiga_concluido_pub_info = investiga_concluido_pub[~investiga_concluido_pub["ID_CONTRATO"].isin(contratos_eliminar)]

# Ahora bien, se utiliza el archivo listado_publicaicones_doi
jajaja = pd.read_excel("listado_publicaciones_doi.xlsx", sheet_name="Hoja1", header=0)
jajaja = jajaja[["DOI"]]


# ABRIR LA TABLA QUE CONTIENE LAS PUBLICACIONES SCOPUS PARA LOS INVESTIGADORES RENACYT
# EN ESTA BASE DE DATOS, SOLO SE MUESTRAN ATRIBUTOS DE LAS PUBLICACIONES
pub_scopus = pd.read_excel("tbl_publicaciones_scopus.xlsx", sheet_name="tbl_scopus_pub", header=0)
pub_scopus.shape
pub_scopus.info()
pub_scopus.columns
pub_scopus["eid"].nunique()
pub_scopus_unica = pub_scopus["eid"].nunique()
print(f"el total de publicaciones scopus únicas son {pub_scopus_unica}")


# Se utiliza el archivo generado por scopus
scopus = pd.read_csv("scopus_export_Jul 15-2026_3f3d649e-c092-4836-8e22-a7690929051a.csv", encoding="latin1")

# ============================================================
# MODELAMIENTO DE TÓPICOS CON TF-IDF + NMF
# Parte de un DataFrame llamado df con columnas:
# - Abstract
# - DOI
# ============================================================

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF


# ============================================================
# 1. LIMPIEZA DE LOS ABSTRACTS
# ============================================================

def corregir_codificacion(texto):
    """
    Corrige errores frecuentes de codificación,
    por ejemplo: El NiÃ±o -> El Niño.
    """
    if pd.isna(texto):
        return ""

    texto = str(texto)

    if any(caracter in texto for caracter in ["Ã", "Â", "â€"]):
        try:
            texto = texto.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

    return texto


def limpiar_abstract(texto):
    """
    Limpia el abstract para el modelamiento de tópicos.
    """
    if pd.isna(texto):
        return ""

    texto = corregir_codificacion(texto)
    texto = texto.lower()

    # Eliminar copyright y contenido editorial final
    texto = re.sub(r"©.*$", " ", texto)
    texto = re.sub(r"copyright.*$", " ", texto)

    # Eliminar enlaces
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto)

    # Conservar letras, espacios y guiones
    texto = re.sub(r"[^a-záéíóúüñ\s-]", " ", texto)

    # Eliminar espacios repetidos
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


scopus["ABSTRACT_LIMPIO"] = scopus["Abstract"].apply(limpiar_abstract)


# Eliminar registros sin abstract o con textos demasiado cortos
df_modelo = scopus[
    scopus["ABSTRACT_LIMPIO"].str.len() > 50
].copy()

print("Publicaciones utilizadas:", len(df_modelo))


# ============================================================
# 2. IDENTIFICAR REFERENCIAS DIRECTAS A ENSO
# ============================================================

patron_enso = (
    r"\benso\b|"
    r"\bel niño\b|"
    r"\bel nino\b|"
    r"\bla niña\b|"
    r"\bla nina\b|"
    r"\bsouthern oscillation\b|"
    r"\bniño 3(?:\.4)?\b|"
    r"\bnino 3(?:\.4)?\b|"
    r"\bcoastal el niño\b|"
    r"\bcoastal el nino\b"
)

df_modelo["MENCIONA_ENSO"] = (
    df_modelo["ABSTRACT_LIMPIO"]
    .str.contains(
        patron_enso,
        regex=True,
        case=False,
        na=False
    )
)

print("\nMenciones directas a ENSO:")
print(df_modelo["MENCIONA_ENSO"].value_counts())


# ============================================================
# 3. CONSTRUIR LA MATRIZ TF-IDF
# ============================================================

vectorizador = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.85,
    max_features=5000,
    sublinear_tf=True
)

matriz_tfidf = vectorizador.fit_transform(
    df_modelo["ABSTRACT_LIMPIO"]
)

print("\nDimensión de la matriz TF-IDF:")
print(matriz_tfidf.shape)


# ============================================================
# 4. APLICAR NMF
# ============================================================

numero_topicos = 8

modelo_nmf = NMF(
    n_components=numero_topicos,
    init="nndsvda",
    random_state=42,
    max_iter=1000
)

matriz_documento_topico = modelo_nmf.fit_transform(
    matriz_tfidf
)


# ============================================================
# 5. EXTRAER LAS PALABRAS PRINCIPALES DE CADA TÓPICO
# ============================================================

terminos = np.array(
    vectorizador.get_feature_names_out()
)

lista_topicos = []

for indice_topico, pesos in enumerate(modelo_nmf.components_):

    indices_principales = pesos.argsort()[-15:][::-1]
    palabras_principales = terminos[indices_principales]

    lista_topicos.append({
        "TOPICO_NUMERO": indice_topico + 1,
        "PALABRAS_CLAVE": ", ".join(palabras_principales)
    })

df_topicos = pd.DataFrame(lista_topicos)

print("\nPalabras principales de cada tópico:")
print(df_topicos.to_string(index=False))


# ============================================================
# 6. ASIGNAR EL TÓPICO DOMINANTE A CADA PUBLICACIÓN
# ============================================================

df_modelo["TOPICO_NUMERO"] = (
    matriz_documento_topico.argmax(axis=1) + 1
)

df_modelo["PESO_TOPICO"] = (
    matriz_documento_topico.max(axis=1)
)

diccionario_palabras = dict(
    zip(
        df_topicos["TOPICO_NUMERO"],
        df_topicos["PALABRAS_CLAVE"]
    )
)

df_modelo["PALABRAS_TOPICO"] = (
    df_modelo["TOPICO_NUMERO"]
    .map(diccionario_palabras)
)


# ============================================================
# 7. REVISAR LOS DOCUMENTOS MÁS REPRESENTATIVOS
# ============================================================

for topico in range(1, numero_topicos + 1):

    print("\n" + "=" * 80)
    print(f"TÓPICO {topico}")
    print(diccionario_palabras[topico])
    print("=" * 80)

    columnas_revision = [
        "PESO_TOPICO",
        "Abstract"
    ]

    if "DOI" in df_modelo.columns:
        columnas_revision.insert(0, "DOI")

    documentos_representativos = (
        df_modelo[
            df_modelo["TOPICO_NUMERO"] == topico
        ]
        .sort_values(
            "PESO_TOPICO",
            ascending=False
        )
        [columnas_revision]
        .head(5)
    )

    print(documentos_representativos.to_string(index=False))


# ============================================================
# 8. ASIGNAR NOMBRES INTERPRETATIVOS
# ============================================================

# IMPORTANTE:
# Revisa primero df_topicos y los documentos representativos.
# Luego modifica este diccionario según el contenido real obtenido.

nombres_topicos = {
    1: "Precipitación extrema y modelamiento atmosférico",
    2: "Oceanografía física y corriente de Humboldt",
    3: "Paleoclima y reconstrucción de ENSO",
    4: "Ecosistemas marinos y pesquerías",
    5: "Manglares, sedimentos y carbono azul",
    6: "Microfísica de nubes y precipitación",
    7: "Variabilidad climática y dinámica ENSO",
    8: "Teledetección y evaluación de desastres"
}

df_modelo["NOMBRE_TOPICO"] = (
    df_modelo["TOPICO_NUMERO"]
    .map(nombres_topicos)
)


# ============================================================
# 9. CREAR LA MATRIZ DOI - TÓPICO
# ============================================================

columnas_doi_topico = [
    "TOPICO_NUMERO",
    "NOMBRE_TOPICO",
    "PESO_TOPICO",
    "PALABRAS_TOPICO",
    "MENCIONA_ENSO",
    "Abstract"
]

if "DOI" in df_modelo.columns:
    columnas_doi_topico.insert(0, "DOI")

df_doi_topico = (
    df_modelo[columnas_doi_topico]
    .sort_values(
        ["TOPICO_NUMERO", "PESO_TOPICO"],
        ascending=[True, False]
    )
    .reset_index(drop=True)
)


# ============================================================
# 10. RESUMEN DE PUBLICACIONES POR TÓPICO
# ============================================================

resumen_topicos = (
    df_modelo
    .groupby(
        ["TOPICO_NUMERO", "NOMBRE_TOPICO"],
        dropna=False
    )
    .agg(
        NUMERO_PUBLICACIONES=("TOPICO_NUMERO", "size"),
        PESO_PROMEDIO=("PESO_TOPICO", "mean"),
        PESO_ACUMULADO=("PESO_TOPICO", "sum"),
        MENCIONES_DIRECTAS_ENSO=("MENCIONA_ENSO", "sum")
    )
    .reset_index()
)

resumen_topicos["PORCENTAJE"] = (
    resumen_topicos["NUMERO_PUBLICACIONES"]
    / resumen_topicos["NUMERO_PUBLICACIONES"].sum()
    * 100
)

resumen_topicos["PALABRAS_CLAVE"] = (
    resumen_topicos["TOPICO_NUMERO"]
    .map(diccionario_palabras)
)

resumen_topicos = (
    resumen_topicos
    .sort_values(
        "NUMERO_PUBLICACIONES",
        ascending=False
    )
    .reset_index(drop=True)
)

print("\nResumen de tópicos:")
print(resumen_topicos.to_string(index=False))


# ============================================================
# 11. GRÁFICO
# ============================================================

df_grafico = resumen_topicos.sort_values(
    "NUMERO_PUBLICACIONES",
    ascending=True
)

fig, ax = plt.subplots(figsize=(11, 6))

barras = ax.barh(
    df_grafico["NOMBRE_TOPICO"],
    df_grafico["NUMERO_PUBLICACIONES"]
)

etiquetas = [
    f"{cantidad} ({porcentaje:.1f}%)"
    for cantidad, porcentaje in zip(
        df_grafico["NUMERO_PUBLICACIONES"],
        df_grafico["PORCENTAJE"]
    )
]

ax.bar_label(
    barras,
    labels=etiquetas,
    padding=4,
    fontsize=9
)

ax.set_xlabel("Número de publicaciones")
ax.set_ylabel("")
ax.set_title(
    "Principales tópicos identificados en las publicaciones"
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.show()


# ============================================================
# 12. EXPORTAR RESULTADOS A EXCEL
# ============================================================

nombre_archivo_salida = "resultados_topicos_nmf.xlsx"

with pd.ExcelWriter(
    nombre_archivo_salida,
    engine="openpyxl"
) as writer:

    df_doi_topico.to_excel(
        writer,
        sheet_name="DOI_por_topico",
        index=False
    )

    resumen_topicos.to_excel(
        writer,
        sheet_name="Resumen_topicos",
        index=False
    )

    df_topicos.to_excel(
        writer,
        sheet_name="Palabras_topicos",
        index=False
    )

print(f"\nArchivo generado: {nombre_archivo_salida}")

























