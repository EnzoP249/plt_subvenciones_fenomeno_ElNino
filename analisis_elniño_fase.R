################################################################################
# PROYECTO PARA UN ANÁLISIS BIBLIOMÉTRICO USANDO R
################################################################################

# Se realiza una limpieza del entorno de trabajo
rm(list = ls())
graphics.off()
cat("\014")

#Se instalan las principales librerias que serán usadas
#install.packages(c(
  #"tidyverse",
  #"igraph",
  #"ggraph",
  #"tidygraph",
  #"readr",
  #"stringr",
  #"lubridate",
  #"scales"
#))

#install.packages("intergraph")
#install.packages("speedglm")

# Se cargan las librerias que serán utilizadas
library(tidyverse)
library(igraph)
library(tidygraph)
library(ggraph)
library(readr)
library(stringr)
library(lubridate)
library(scales)
library(btergm)
library(network)
library(sna)
library(readr)
library(dplyr)
library(tidyr)
library(network)
library(ergm)
library(btergm)
library(intergraph)
library(speedglm)

# Se define el directorio de forma manual
setwd("C:/Users/Enzo/OneDrive/Documentos/Trabajo Banco Mundial/proyecto_fenomeno_nino")
getwd()

# Se cargan los dos archivos que serán usados
nodos <- read_csv("authors.csv")
autor_publicacion <- read_csv("author_publication.csv")
produccion <- read_csv("produccion_cientifica.csv")

# Autores
nodos <- nodos %>%
  transmute(
    name = trimws(as.character(Author_id)),
    Author_name,
    Affiliations
  ) %>%
  distinct(name, .keep_all = TRUE)


# Relaciones autor-publicación
autor_publicacion <- autor_publicacion %>%
  mutate(
    Author_id = trimws(as.character(Author_id)),
    EID = trimws(as.character(EID)),
    Year = as.integer(Year)
  )


# ============================================================
# 2. RED BIPARTITA AUTOR–PUBLICACIÓN
# ============================================================

df_bip_edges <- autor_publicacion %>%
  filter(
    !is.na(Author_id),
    !is.na(EID),
    !is.na(Year),
    Year >= 2010,
    Year <= 2024
  ) %>%
  distinct(Author_id, EID, Year)


# ============================================================
# 3. DIAGNÓSTICOS
# ============================================================

# ¿Un EID aparece asociado a más de un año?
eid_multiple_years <- df_bip_edges %>%
  distinct(EID, Year) %>%
  count(EID, name = "n_years") %>%
  filter(n_years > 1)

print(eid_multiple_years)


# Número de autores por publicación
autores_por_publicacion <- df_bip_edges %>%
  distinct(EID, Author_id) %>%
  count(EID, name = "n_autores") %>%
  arrange(desc(n_autores))

print(head(autores_por_publicacion, 20))


# Número de publicaciones por año
publicaciones_por_anio <- df_bip_edges %>%
  distinct(EID, Year) %>%
  count(Year, name = "n_publicaciones")

print(publicaciones_por_anio)


# Número de autores activos por año
autores_por_anio <- df_bip_edges %>%
  distinct(Author_id, Year) %>%
  count(Year, name = "n_autores")

print(autores_por_anio)


# ============================================================
# 4. CONSTRUCCIÓN TEMPORAL DEL UNIVERSO DE NODOS
# ============================================================
#
# IMPORTANTE:
#
# En cada año t:
#
#   autores = autores que ya aparecieron hasta t
#   papers  = publicaciones que ya aparecieron hasta t
#
# Por tanto:
#
#   V_t = A_(<=t) U P_(<=t)
#
# Esto evita introducir autores/papers futuros como aislados.
# ============================================================

years <- 2010:2024

networks_bip <- list()

for (y in years) {
  
  # ----------------------------------------------------------
  # Nodos disponibles hasta el año y
  # ----------------------------------------------------------
  
  authors_y <- df_bip_edges %>%
    filter(Year <= y) %>%
    distinct(Author_id) %>%
    pull(Author_id)
  
  papers_y <- df_bip_edges %>%
    filter(Year <= y) %>%
    distinct(EID) %>%
    pull(EID)
  
  
  # ----------------------------------------------------------
  # Universo de nodos del año
  # ----------------------------------------------------------
  
  vertices_y <- data.frame(
    name = c(authors_y, papers_y),
    type = c(
      rep("author", length(authors_y)),
      rep("paper", length(papers_y))
    ),
    stringsAsFactors = FALSE
  )
  
  
  n_authors_y <- length(authors_y)
  
  
  # ----------------------------------------------------------
  # Inicializar red bipartita
  # ----------------------------------------------------------
  
  net <- network.initialize(
    n = nrow(vertices_y),
    bipartite = n_authors_y,
    directed = FALSE
  )
  
  
  set.vertex.attribute(
    net,
    "vertex.names",
    vertices_y$name
  )
  
  net %v% "type" <- vertices_y$type
  
  
  # ----------------------------------------------------------
  # Aristas DEL AÑO y
  # ----------------------------------------------------------
  
  ed_y <- df_bip_edges %>%
    filter(Year == y)
  
  
  if (nrow(ed_y) > 0) {
    
    from_idx <- match(
      ed_y$Author_id,
      vertices_y$name
    )
    
    to_idx <- match(
      ed_y$EID,
      vertices_y$name
    )
    
    valid <- !is.na(from_idx) & !is.na(to_idx)
    
    if (any(valid)) {
      
      add.edges(
        net,
        tail = from_idx[valid],
        head = to_idx[valid]
      )
    }
  }
  
  
  networks_bip[[as.character(y)]] <- net
  
  
  # ----------------------------------------------------------
  # Diagnóstico
  # ----------------------------------------------------------
  
  n_authors_total <- sum(vertices_y$type == "author")
  n_papers_total  <- sum(vertices_y$type == "paper")
  
  n_authors_active <- sum(
    network.size(net) > 0 &
      vertices_y$type == "author"
  )
  
  cat(
    "\nAño:", y,
    "\n  Autores acumulados:", n_authors_total,
    "\n  Papers acumulados:", n_papers_total,
    "\n  Aristas:", network.edgecount(net),
    "\n"
  )
}


# ============================================================
# 5. ORDEN TEMPORAL PARA BTERGM
# ============================================================

years_memoria <- 2010:2024
years_modelo <- 2011:2024

nets_bip_ordered <- networks_bip[
  as.character(years_memoria)
]

nets_bip_modelo <- nets_bip_ordered[
  as.character(years_modelo)
]

# ============================================================
# 6. PRODUCTIVIDAD ACUMULADA
# ============================================================

prod_total <- rowSums(
  produccion[, as.character(years_memoria)],
  na.rm = TRUE
)

names(prod_total) <- as.character(produccion$id_nodo)


# Top 25 %
umbral_75 <- quantile(
  prod_total,
  0.75,
  na.rm = TRUE
)

prod_alta_named <- as.numeric(
  prod_total >= umbral_75
)

names(prod_alta_named) <- names(prod_total)


# ============================================================
# 7. ATRIBUTOS DE LOS AUTORES
# ============================================================

for (y in years_memoria) {
  
  net <- nets_bip_ordered[[as.character(y)]]
  
  vnames <- network.vertex.names(net)
  
  is_author <- net %v% "type" == "author"
  
  author_names <- vnames[is_author]
  
  
  # ----------------------------------------------------------
  # Productividad del año
  # ----------------------------------------------------------
  
  idx <- match(
    author_names,
    as.character(produccion$id_nodo)
  )
  
  prod_y <- produccion[[as.character(y)]][idx]
  
  prod_y[is.na(prod_y)] <- 0
  
  
  # ----------------------------------------------------------
  # Indicador de alta productividad
  # ----------------------------------------------------------
  
  prod_alta_y <- prod_alta_named[author_names]
  
  prod_alta_y[is.na(prod_alta_y)] <- 0
  
  
  # ----------------------------------------------------------
  # Asignar atributos únicamente a autores
  # ----------------------------------------------------------
  
  prod_full <- rep(NA_real_, network.size(net))
  
  prod_alta_full <- rep(NA_real_, network.size(net))
  
  
  prod_full[is_author] <- prod_y
  
  prod_alta_full[is_author] <- prod_alta_y
  
  
  net %v% "produccion" <- prod_full
  
  net %v% "prod_alta" <- prod_alta_full
  
  
  nets_bip_ordered[[as.character(y)]] <- net
}


# Actualizar redes del modelo
nets_bip_modelo <- nets_bip_ordered[
  as.character(years_modelo)
]


# ============================================================
# 8. COMPROBACIONES ANTES DEL BTERGM
# ============================================================

# Tamaño de las redes
network_sizes <- data.frame(
  Year = years,
  Nodes = sapply(networks_bip, network.size),
  Edges = sapply(networks_bip, network.edgecount)
)

print(network_sizes)


# Proporción de aislados
isolated_stats <- data.frame(
  Year = years,
  Isolates = sapply(
    networks_bip,
    function(x) sum(network.size(x) > 0 & degree(x) == 0)
  )
)

isolated_stats$Prop_isolates <-
  isolated_stats$Isolates /
  network_sizes$Nodes

print(isolated_stats)


# ============================================================
# 9. MODELO BTERGM bipartito BASE
# ============================================================
set.seed(42)

m0_bip <- btergm(
  nets_bip_modelo ~
    edges +
    gwb1degree(
      0.6,
      fixed = TRUE
    ) +
    gwb2degree(
      0.6,
      fixed = TRUE
    ),
  R = 1000
)


# ============================================================
# 10. RESULTADOS
# ============================================================
summary(m0_bip)


set.seed(42)

m_final_bip <- btergm(
  nets_bip_modelo ~
    edges +
    gwb1degree(0.6, fixed = TRUE) +
    gwb2degree(0.6, fixed = TRUE) +
    gwb1dsp(0.6, fixed = TRUE) +
    b1factor("prod_alta") +
    b1nodematch("prod_alta"),
  R = 1000
)

summary(m_final_bip)




