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
#install.packages("bipartite")


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
library(igraph)
library(bipartite)
library(knitr)


# Se define el directorio de forma manual y formal
setwd("C:/Users/Enzo/OneDrive/Documentos/Trabajo Banco Mundial/proyecto_fenomeno_nino")
getwd()

# Se cargan los tres archivos que serán usados
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

# Se observa un caso particular en el dataframe autor_publicacion
View(autor_publicacion %>% filter (Author_id == "58787423400"))

# Se construye una red bipartita de autores científicos y publicaciones 
df_bip_edges <- autor_publicacion %>%
  filter(
    !is.na(Author_id),
    !is.na(EID),
    !is.na(Year),
    Year >= 2010,
    Year <= 2024
  ) %>%
  distinct(Author_id, EID, Year)

class(df_bip_edges)

# Se calcula la producción científica anual
publicaciones_por_anio <- df_bip_edges %>%
  distinct(EID, Year) %>%
  count(Year, name = "n_publicaciones")

print(publicaciones_por_anio)

# Se calcula producción científica total
suma_total_publicaciones <- sum(publicaciones_por_anio$n_publicaciones)
print(suma_total_publicaciones)


# Número de autores por publicación
autores_por_publicacion <- df_bip_edges %>%
  distinct(EID, Author_id) %>%
  count(EID, name = "n_autores") %>%
  arrange(desc(n_autores))

print(head(autores_por_publicacion, 20))

# Numero de autores únicos por año
autores_por_anio <- df_bip_edges %>%
  distinct(Author_id, Year) %>%
  count(Year, name = "n_autores_unicos")

print(autores_por_anio)


################################################################################
# Se calcula la cantidad de publicaciones con autoria masiva por año
# Definir el umbral (cámbielo según su criterio o campo de estudio)
################################################################################
umbral_masivo <- 120

# Calcular publicaciones masivas por año
publicaciones_masivas <- df_bip_edges %>%
  group_by(Year, EID) %>%
  summarise(total_autores = n(), .groups = "drop") %>%
  mutate(es_masiva = total_autores >= umbral_masivo) %>%
  group_by(Year) %>%
  summarise(
    total_publicaciones = n(),
    publicaciones_masivas = sum(es_masiva),
    porcentaje_masivas = (publicaciones_masivas / total_publicaciones) * 100
  )

print(publicaciones_masivas)

sum(publicaciones_masivas$publicaciones_masivas) / sum(publicaciones_masivas$total_publicaciones) # 10 / 443 = 2.25%

################################################################################
# Se calcula el número de autores por cada paper de autoria masiva por año
################################################################################

autores_por_paper <- df_bip_edges %>%
  group_by(Year, EID) %>%
  summarise(n_autores = n_distinct(Author_id), .groups="drop")

# 2. define masiva - pon tu corte real, ej 100 autores
corte_masiva <- 120

masivas <- autores_por_paper %>%
  filter(n_autores >= corte_masiva) %>%
  arrange(Year, desc(n_autores))

masivas

################################################################################
# Calcular el total de enlaces únicos (autor-publicación) por año
################################################################################

enlaces_por_anio <- df_bip_edges %>%
  count(Year, name = "total_enlaces")

# Visualizar el resultado
print(enlaces_por_anio)

################################################################################
# ¿Un EID aparece asociado a más de un año?
################################################################################

eid_multiple_years <- df_bip_edges %>%
  distinct(EID, Year) %>%
  count(EID, name = "n_years") %>%
  filter(n_years > 1)

print(eid_multiple_years)

################################################################################
# Número de autores activos por año
################################################################################

autores_por_anio <- df_bip_edges %>%
  distinct(Author_id, Year) %>%
  count(Year, name = "n_autores")

print(autores_por_anio)

################################################################################
# Se crea un objeto graph bipartito usando el dataframe df_bip_edges
################################################################################

g <- graph_from_data_frame(df_bip_edges[,c("EID","Author_id")], directed=FALSE)
V(g)$type <- V(g)$name %in% df_bip_edges$Author_id
is_bipartite(g) # TRUE
class(g)


# 1. Básico global
n_papers <- sum(!V(g)$type)
n_autores <- sum(V(g)$type)

M <- as_biadjacency_matrix(g) # necesitas esto para bipartite

################################################################################
# 2. Nivel de densidad de la red
################################################################################
densidad_bip <- ecount(g) / (n_papers * n_autores)
print(densidad_bip)

################################################################################
# Se analizan descriptivos de la matriz biadyacente
################################################################################

bipartite::networklevel(M_dense, index=c("connectance","web asymmetry","nestedness","ISA"))

tab <- data.frame(
  Indice = c("Connectance", "Web asymmetry", "Nestedness", "Interaction Strength Asymmetry"),
  Valor = c(0.00503, 0.7466, 0.1617, 0.0000),
  Interpretacion = c(
    "Red hiper-dispersa (0.5% de enlaces posibles)",
    "Fuerte desbalance: muchos más autores que papers",
    "Baja anidación: sin núcleo-periferia claro",
    "Red no pesada (matriz binaria)"
  )
)

kable(tab, digits=4, caption="Descriptivos de la matriz biadyacente [papers x autores]")


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

# Se elabora el modelo final
set.seed(42)

m_final_bip <- btergm(
  nets_bip_modelo ~
    edges +
    gwb1degree(0.6, fixed = TRUE) +
    gwb2degree(0.6, fixed = TRUE) +
    gwb1dsp(0.6, fixed = TRUE) +
    b1factor("prod_alta") +
    b1nodematch("prod_alta"),
  R = 5000
)

summary(m_final_bip)

gof_bip <- btergm::gof(m_final_bip, nsim = 100)
plot(gof_bip)













library(dplyr)
library(purrr)

# ============================================================
# 1. AUTORES DE CADA PUBLICACIÓN
# ============================================================

equipos <- autor_publicacion %>%
  mutate(
    Author_id = trimws(as.character(Author_id)),
    EID = trimws(as.character(EID)),
    Year = as.integer(Year)
  ) %>%
  filter(
    !is.na(Author_id),
    !is.na(EID),
    !is.na(Year),
    Year >= 2010,
    Year <= 2024
  ) %>%
  distinct(Year, EID, Author_id) %>%
  group_by(Year, EID) %>%
  summarise(
    autores = list(unique(Author_id)),
    n_autores = n_distinct(Author_id),
    .groups = "drop"
  )


# ============================================================
# 2. COMPARAR CADA PUBLICACIÓN DE t CON LAS DE t+1
# ============================================================

persistencia <- equipos %>%
  rename(
    year_t = Year,
    eid_t = EID,
    autores_t = autores,
    n_autores_t = n_autores
  ) %>%
  left_join(
    equipos %>%
      rename(
        year_t1 = Year,
        eid_t1 = EID,
        autores_t1 = autores,
        n_autores_t1 = n_autores
      ),
    by = character()
  ) %>%
  filter(year_t1 == year_t + 1) %>%
  mutate(
    autores_comunes = map2_int(
      autores_t,
      autores_t1,
      ~ length(intersect(.x, .y))
    ),
    
    proporcion_persistencia =
      autores_comunes / n_autores_t
  )


# ============================================================
# 3. ELEGIR LA PUBLICACIÓN DE t+1 CON MAYOR SOLAPAMIENTO
# ============================================================

persistencia_max <- persistencia %>%
  group_by(year_t, eid_t) %>%
  slice_max(
    order_by = proporcion_persistencia,
    n = 1,
    with_ties = FALSE
  ) %>%
  ungroup()


# ============================================================
# 4. RESULTADOS
# ============================================================

resultado <- persistencia_max %>%
  dplyr::select(
    year_t,
    eid_t,
    n_autores_t,
    eid_t1,
    n_autores_t1,
    autores_comunes,
    proporcion_persistencia
  ) %>%
  arrange(year_t, desc(proporcion_persistencia))

print(resultado)


