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
library(intergraph)

# Se define el directorio de forma manual
setwd("C:/Users/Enzo/OneDrive/Documentos/Trabajo Banco Mundial/proyecto_fenomeno_nino")
getwd()

# Se cargan los dos archivos que serán usados
nodos <- read_csv("authors.csv")
autor_publicacion <- read_csv("author_publication.csv")
produccion <- read_csv("produccion_cientifica.csv")

# Se realiza una verificación previa
head(nodos)
head(autor_publicacion)
head(produccion)

# Se verifica presencia de duplicados
sum(duplicated(nodos$Author_id))
sum(duplicated(autor_publicacion))
sum(duplicated(autor_publicacion[c("EID", "Author_id")]))

# Número de autores
n_distinct(nodos$Author_id)

# Número de publicaciones
n_distinct(autor_publicacion$EID)

# Número de registros autor-publicación
nrow(autor_publicacion)

# Se analiza la cantidad de publicaciones por autor distinto
autores_por_publicacion <- autor_publicacion %>%
  distinct(EID, Author_id) %>%
  count(EID, name = "n_autores") %>%
  arrange(desc(n_autores))

head(autores_por_publicacion, 20)

# Se cambia el nombre del identificador del objeto nodo por name
nodos <- nodos %>%
  transmute(
    name = as.character(Author_id),
    Author_name,
    Affiliations
  )

# En el dataframe autor_publicacion se cambia el tipo de dato de la columna author_id
autor_publicacion <- autor_publicacion %>%
  mutate(Author_id = as.character(Author_id))

############################################################
# Se construye el dataframe de los enlaces
############################################################

df_edges_year <- autor_publicacion %>%
  distinct(EID, Author_id, Year) %>% 
  group_by(EID, Year) %>% # <- agrupas por Year también
  filter(n() >= 2) %>%
  summarise(
    pares = list(combn(as.character(Author_id), 2, simplify=FALSE)),
    .groups="drop"
  ) %>%
  tidyr::unnest_longer(pares) %>%
  transmute(
    Year,
    from = pmin(purrr::map_chr(pares,1), purrr::map_chr(pares,2)),
    to   = pmax(purrr::map_chr(pares,1), purrr::map_chr(pares,2))
  ) %>%
  count(Year, from, to, name="weight")

# Número de diadas creadas en total
n_distinct(df_edges_year)


# Ahora si:
# df_edges_year %>% filter(Year %in% 2010:2012) -> para construir tu edgecov_2013
# df_edges_year %>% filter(Year >= 2013) -> para tus redes dependientes 2013-2024

faltan <- setdiff(unique(c(df_edges_year$from, df_edges_year$to)), nodos$name)
length(faltan)
head(faltan)


############################################################
# Se construyen los grafos no dirigidos y las redes
############################################################
vertices_df <- data.frame(name = trimws(as.character(nodos$name)))

graphs_year <- list()      # para tabla general
networks_list <- list()    # para btergm

for(y in 2010:2024){  # <-- cambié a 2010
  df_y <- df_edges_year %>% 
    filter(Year == y) %>%
    select(from,to)
  
  g <- graph_from_data_frame(df_y, vertices=vertices_df, directed=FALSE)
  graphs_year[[as.character(y)]] <- g
  networks_list[[as.character(y)]] <- intergraph::asNetwork(g)
}

# GENERAL para tu descriptivo
graphs_year[["GENERAL"]] <- graph_from_data_frame(
  df_edges_year %>% distinct(from,to), vertices=vertices_df, directed=FALSE
)


############################################################
# 1. TABLA GENERAL
############################################################
df_general <- lapply(names(graphs_year), function(y){
  g <- graphs_year[[y]]
  comp <- igraph::components(g)
  deg <- igraph::degree(g)
  data.frame(
    Red = y,
    N_nodos = igraph::vcount(g),
    N_conectados = sum(deg>0),
    N_aristas = igraph::ecount(g),
    Grado_prom = round(mean(deg),2),
    Grado_max = max(deg),
    Densidad = igraph::edge_density(g),
    N_componentes = comp$no,
    Tam_comp_principal = max(comp$csize),
    Prop_comp_principal = max(comp$csize)/igraph::vcount(g),
    Clustering_global = igraph::transitivity(g, type="global"),
    Aislados = sum(deg==0)
  )
}) %>% bind_rows()

print(df_general)

############################################################
# GRÁFICOS EVOLUTIVOS
############################################################
df_plot <- df_general %>% filter(Red!="GENERAL") %>% mutate(Year=as.integer(as.character(Red)))

ggplot(df_plot, aes(Year, N_aristas)) + geom_line() + geom_point() + theme_minimal() + labs(title="Evolución N° aristas")
ggplot(df_plot, aes(Year, Grado_prom)) + geom_line() + geom_point() + theme_minimal() + labs(title="Grado promedio")
ggplot(df_plot, aes(Year, Clustering_global)) + geom_line() + geom_point() + theme_minimal() + labs(title="Clustering global")
ggplot(df_plot, aes(Year, Prop_comp_principal)) + geom_line() + geom_point() + theme_minimal() + labs(title="Proporción componente principal")


# -------------------------------------------------
# 0. Ventanas temporales
# -------------------------------------------------
# Memoria necesita t-1, por eso memoria empieza en 2010
# Modelo estima 2011:2024 = 14 redes, 13 transiciones
years_memoria <- 2010:2024
years_modelo <- 2011:2024

nets_ordered <- networks_list[as.character(years_memoria)]
nets_modelo <- nets_ordered[as.character(years_modelo)]
length(nets_modelo) # 14, no 13

# -------------------------------------------------
# 1. Élite estática top 25% - definición teórica
# -------------------------------------------------
# Élite por producción acumulada, no flotante por año
prod_total <- rowSums(produccion[, as.character(years_memoria)], na.rm = TRUE)
names(prod_total) <- produccion$id_nodo

umbral_75 <- quantile(prod_total, 0.75, na.rm = TRUE)
prod_alta_named <- as.numeric(prod_total >= umbral_75)
names(prod_alta_named) <- produccion$id_nodo

# -------------------------------------------------
# 2. Asignar atributos a cada red
# -------------------------------------------------
for(y in years_memoria){
  net <- nets_ordered[[as.character(y)]]
  idx <- match(vertices_df$name, produccion$id_nodo)
  
  prod_y <- produccion[[as.character(y)]][idx]
  prod_y[is.na(prod_y)] <- 0
  
  prod_alta_y <- prod_alta_named[idx]
  prod_alta_y[is.na(prod_alta_y)] <- 0
  
  net %v% "produccion" <- prod_y
  net %v% "produccion_log" <- log1p(prod_y)
  net %v% "prod_alta" <- prod_alta_y
  
  nets_ordered[[as.character(y)]] <- net
}
nets_modelo <- nets_ordered[as.character(years_modelo)]

# -------------------------------------------------
# 3. Diagnóstico Lotka / justificación isolates
# -------------------------------------------------
isolates_year <- sapply(nets_modelo, function(net) sum(degree(net, gmode="graph") == 0))
isolates_year # ~2800 por año

all_deg <- unlist(lapply(nets_modelo, function(net) degree(net, gmode="graph")))
table(all_deg) # 36,799 en grado 0 + picos en 369, 391, 467, 500, 539 = tus masivas

# Justifica isolates, no gwdegree: Lotka es para ceros, no para curva 1/n2

# -------------------------------------------------
# 4. Control autoría masiva - 9 papers de tu foto
# -------------------------------------------------
# 540, 501, 474, 469, 468, 468, 423, 392, 370 autores
# No se borran, se absorben con edgecov ponderado log

masiva_mat_list <- lapply(nets_modelo, function(net){
  n <- network.size(net)
  mat <- matrix(0, n, n)
  deg <- degree(net, gmode="graph")
  cand <- unique(deg[deg >= 125])
  
  for(d in cand){
    idx <- which(deg == d)
    if(length(idx) > 2){
      sub <- as.matrix(net)[idx, idx]
      if(sum(sub) == length(idx)*(length(idx)-1)){
        # peso log: 370->0.82, 540->0.76, triada 3->1
        # así beta queda ~30 y no 11835, y gwesp no se escapa a 221
        w <- log(125) / log(length(idx))
        mat[idx, idx] <- w
      }
    }
  }
  diag(mat) <- 0
  mat
})

# chequeo obligatorio antes de btergm
stopifnot(length(masiva_mat_list) == length(nets_modelo)) # 14 == 14
stopifnot(all(!sapply(masiva_mat_list, is.null)))

# -------------------------------------------------
# 5. Modelo final - H2 cierre estratificado neto de big science
# -------------------------------------------------
set.seed(42)

modelo_final_elite <- btergm(nets_modelo ~
  edges + isolates +
  edgecov(masiva_mat_list) +
  gwesp(0.6, fixed=TRUE) +
  nodefactor("prod_alta") + nodematch("prod_alta") +
  memory(type="stability", lag=1), R=1000)


summary(modelo_final_elite)





















 

