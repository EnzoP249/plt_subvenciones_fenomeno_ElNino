###############################################################################
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

# Ver la versión exacta de ergm instalada
packageVersion("ergm")

# Listar todos los términos con prefijo b1/b2 disponibles en tu versión
grep("^b1|^b2", ergm::search.ergmTerms(), value = TRUE)


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
res <- bipartite::networklevel(M, index=c("connectance","web asymmetry","nestedness","ISA"))

tab <- data.frame(
  Indice = names(res),
  Valor = as.numeric(res),
  Interpretacion = c(
    "Red hiper-dispersa (0.5% de enlaces)",
    "Fuerte desbalance: muchos más autores que papers",
    "Baja anidación: sin núcleo-periferia",
    "Matriz binaria"
  )
)

knitr::kable(tab, digits=4, caption="Descriptivos de la matriz diadyacente [papers x autores]")

# ============================================================
# CONSTRUCCIÓN DE REDES ANUALES INDEPENDIENTES PARA POOLED ERGM
# ============================================================
# Cada red Y_t contiene únicamente los autores y papers 
# que participaron en el año t, reflejando el espacio relacional 
# real sin sesgos de acumulación de aislados.
# ============================================================

years <- 2010:2024
networks_bip <- list()

for (y in years) {
  
  # 1. Filtrar únicamente las aristas que se formaron en el año y
  ed_y <- df_bip_edges %>%
    filter(Year == y)
  
  # Si no hay aristas en ese año, omitir o continuar
  if (nrow(ed_y) == 0) next
  
  # 2. Extraer ÚNICAMENTE los actores activos en el año y
  authors_y <- unique(ed_y$Author_id)
  papers_y  <- unique(ed_y$EID)
  
  # 3. Definir el universo de nodos del año y
  vertices_y <- data.frame(
    name = c(authors_y, papers_y),
    type = c(
      rep("author", length(authors_y)),
      rep("paper", length(papers_y))
    ),
    stringsAsFactors = FALSE
  )
  
  n_authors_y <- length(authors_y)
  n_papers_y  <- length(papers_y)
  
  # 4. Inicializar la red bipartita para el año y
  #    IMPORTANTE en statnet:
  #    bipartite = n_authors_y establece que los primeros 
  #    'n_authors_y' nodos de la lista pertenecen al Modo 1 (Autores).
  net <- network.initialize(
    n = nrow(vertices_y),
    bipartite = n_authors_y,
    directed = FALSE
  )
  
  # Asignar nombres y tipo de nodo
  set.vertex.attribute(net, "vertex.names", vertices_y$name)
  net %v% "type" <- vertices_y$type
  
  # 5. Mapear e insertar las aristas en el objeto network
  from_idx <- match(ed_y$Author_id, vertices_y$name)
  to_idx   <- match(ed_y$EID, vertices_y$name)
  
  valid <- !is.na(from_idx) & !is.na(to_idx)
  
  if (any(valid)) {
    add.edges(
      net,
      tail = from_idx[valid],
      head = to_idx[valid]
    )
  }
  
  # 6. Almacenar la red limpia en la lista
  networks_bip[[as.character(y)]] <- net
  
  # ----------------------------------------------------------
  # Diagnóstico en consola
  # ----------------------------------------------------------
  cat(
    "Año:", y,
    "| Autores activos:", n_authors_y,
    "| Papers activos:", n_papers_y,
    "| Aristas:", network.edgecount(net),
    "\n"
  )
}

# Se analiza la clase del objeto networks_bip
class(networks_bip)
class(networks_bip[["2023"]])

# ============================================================
# COMPROBACIONES ANTES DEL BTERGM
# ============================================================

# Tamaño de las redes
network_sizes <- data.frame(
  Year = years,
  Nodes = sapply(networks_bip, network.size),
  Edges = sapply(networks_bip, network.edgecount)
)

print(network_sizes)

################################################################################
# 1. Valores candidatos para el parámetro de decaimiento
################################################################################

decays <- c(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7,0.8, 0.9, 1)

modelos <- vector("list", length(decays))
aics <- numeric(length(decays))
log_pl <- numeric(length(decays))

################################################################################
# 2. Semilla para reproducibilidad
################################################################################

set.seed(42)

################################################################################
# 3. Estimación de los modelos
################################################################################

for (i in seq_along(decays)) {
  
  d <- decays[i]
  
  cat("\n")
  cat("============================================================\n")
  cat("Estimando modelo con decay =", d, "\n")
  cat("============================================================\n")
  
  modelos[[i]] <- btergm(
    networks_bip ~
      edges +
      gwb1degree(
        decay = 0.6,
        fixed = TRUE
      ) +
      gwb2degree(
        decay = 0.2,
        fixed = TRUE
      ) +
      gwb1dsp(
        decay = d,
        fixed = TRUE
      ),
    R = 1000
  )
  
  ##############################################################################
  # 4. Extraer la pseudoverosimilitud
  #
  # btergm estima mediante MPLE. El objeto almacena:
  #   @response -> variable respuesta
  #   @effects  -> matriz de variables explicativas
  #   @weights  -> pesos de las observaciones
  #
  # Por tanto, reconstruimos la log-pseudoverosimilitud del modelo logístico.
  ##############################################################################
  
  beta <- coef(modelos[[i]])
  
  X <- as.matrix(modelos[[i]]@effects)
  
  y <- as.numeric(modelos[[i]]@response)
  
  w <- modelos[[i]]@weights
  
  ##############################################################################
  # 5. Calcular el predictor lineal
  ##############################################################################
  
  eta <- as.vector(X %*% beta)
  
  ##############################################################################
  # 6. Probabilidades estimadas
  ##############################################################################
  
  p <- plogis(eta)
  
  ##############################################################################
  # 7. Evitar log(0) por estabilidad numérica
  ##############################################################################
  
  eps <- .Machine$double.eps
  
  p <- pmax(
    pmin(p, 1 - eps),
    eps
  )
  
  ##############################################################################
  # 8. Log-pseudoverosimilitud
  ##############################################################################
  
  log_pl[i] <- sum(
    w * (
      y * log(p) +
        (1 - y) * log(1 - p)
    )
  )
  
  ##############################################################################
  # 9. Número de parámetros
  ##############################################################################
  
  k <- length(beta)
  
  ##############################################################################
  # 10. AIC de la pseudoverosimilitud
  ##############################################################################
  
  aics[i] <- 2 * k - 2 * log_pl[i]
  
  ##############################################################################
  # 11. Mostrar resultados
  ##############################################################################
  
  cat(
    sprintf(
      "Decay gwb1dsp: %.1f | Log-PL: %.4f | k: %d | AIC-PL: %.4f\n",
      d,
      log_pl[i],
      k,
      aics[i]
    )
  )
}

################################################################################
# 12. Tabla comparativa
################################################################################

resultados_decay <- data.frame(
  decay_gwb1dsp = decays,
  log_pseudolikelihood = log_pl,
  k = sapply(modelos, function(x) length(coef(x))),
  AIC_PL = aics
)

resultados_decay <- resultados_decay[
  order(resultados_decay$AIC_PL),
]

rownames(resultados_decay) <- NULL

################################################################################
# 13. Mostrar tabla
################################################################################
print(resultados_decay)

################################################################################
# 14. Seleccionar el modelo con menor AIC
################################################################################

idx_optimo <- which.min(aics)

decay_optimo <- decays[idx_optimo]

m_final_bip <- modelos[[idx_optimo]]

################################################################################
# 15. Mostrar modelo seleccionado
################################################################################

cat("\n")
cat("============================================================\n")
cat("MODELO SELECCIONADO\n")
cat("============================================================\n")

cat(
  sprintf(
    "Decay óptimo de gwb1dsp: %.1f\n",
    decay_optimo
  )
)

cat(
  sprintf(
    "AIC de pseudoverosimilitud: %.4f\n",
    aics[idx_optimo]
  )
)

cat("============================================================\n\n")

################################################################################
# 16. Resumen del modelo final
################################################################################
summary(m_final_bip)


################################################################################
# Se aplica bonda de ajuste
################################################################################
gof_bip_01 <- btergm::gof(
  m_final_bip, 
  nsim = 100,
  bipartite = TRUE,                     # Forzar estadísticas de evaluación bipartitas
  statistics = c(b1deg, b2deg, dsp, geodist) # Evaluar explícitamente ambos modos
)

# Limpiar el dispositivo gráfico e imprimir las nuevas simulaciones
dev.off() # Cierra la ventana gráfica previa cargada en memoria
plot(gof_bip_01)


################################################################################
# Resultados post estimación
################################################################################
# 1. Unir la tabla consigo misma para encontrar todos los pares de autores 
# que co-firmaron la misma publicación en el mismo año.
# Usamos inner_join para que solo queden pares que compartan EID y Year.
pares_autores <- df_bip_edges %>%
  inner_join(df_bip_edges, 
             by = c("EID", "Year"), 
             relationship = "many-to-many") %>%
  # Para evitar duplicados (Autor1-Autor2 y Autor2-Autor1) y auto-lazos (mismo autor)
  filter(Author_id.x < Author_id.y) %>%
  # Contamos cuántas publicaciones distintas comparte cada par de autores
  count(Author_id.x, Author_id.y, name = "publicaciones_compartidas") %>%
  arrange(desc(publicaciones_compartidas))

# 2. Ver los 10 pares de autores que más publicaciones comparten (los "compañeros estrella")
top_companeros <- pares_autores %>%
  slice_max(publicaciones_compartidas, n = 30)

print(top_companeros)






