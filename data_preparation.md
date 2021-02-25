# Informations sur la préparation des données 

Afin de faire tourner le script `main_processing.py`, un certain nombre de fichiers contenant des données sont nécessaires. 

## Données de fréquentation 

Elles doivent être structurées sous forme de csv avec trois colonnes necessaires:
  - `--site_nom`: colonne indiquant le nom de l'établissement
  - `--site_type`: colonne indiquant le type d'établissmeent (elementaire, maternelle)
  - `--date`: colonne contenant la date au format `%Y-%m-%d`
  
 Ces trois colonnes permettent de créer un indice unique de fréquentation (1 observation = 1 restaurant scolaire (site_nom + site_type) + 1 date) 
  
 ## Données sur les effectifs des écoles

Elles doivent être structurées sous forme de csv avec deux colonnes necessaires:
  - `--ecole`: colonne indiquant le nom de l'établissement
  - `--effectif`: colonne indiquant le nombre d'élèves inscrits dans l'établissement lors de l'année scolaire
   - `--annee_scolaire`: colonne indiquant l'année scolaire
   
N.B: les noms d'école peuvent être différents entre les données de fréquentation et d'effectif mais dans ce cas, il est nécessaire de modifier la fonction `match_etab` du fichier `processing.py`


## Données sur les vacances scolaires

Elles doivent être structurées sous forme de csv et contenir seulement trois colonnes:
  - `--nom`: le nom des vacances en question
  - `--date_start`: date à laquelle commencent les vacances sous format `%Y-%m-%d`
  - `--date_end`: date à laquelle finissent les vacances sous format `%Y-%m-%d`

## Données sur les menus

Il existe deux types de fichiers pour gérer les formats donnés par la métropole de Nantes mais il est possbile d'en utilisr un seul.
 - Un fichier csv en encoding `latin` avec une colonne `date` sous format `%Y-%m-%d` ("menus_2011_2015.csv")
 - Un fichier csv en encoding `latin` avec une colonne `Date` sous format `%d/%m/%Y` ("menus_2016_2019.csv")

Les deux fichiers contiennent une colonne `menus` sous format string

## Données sur les grèves spécifiques à votre métropole 

Elles doivent être structurées sous forme de csv et contenir seulement deux colonnes:
  - `--date`: colonne contenant la date au format `%Y-%m-%d`
  - `--ind`: colonne indiquant de manière binaire s'il y a eu grève ou non

## Données sur les grèves SNCF

Nous avons trouvé le fichier de grèves sncf mouvements-sociaux-depuis-2002 sur le site data.sncf.com, vous pouvez récupérer ce fichier via l'url suivante: https://data.sncf.com/explore/dataset/mouvements-sociaux-depuis-2002/

## Données sur les épidémies

Ces données ont été récupérées via le réseau sentinelles via l'url suivante: https://www.sentiweb.fr/france/fr/?page=table

Vous pouvez ensuite choisir les différentes épidémies pour lesquelles vous souhaitez les indicateurs dans le menu déroulant. 
Nous avons sélectionné les épidémies suivantes:
 - la grippe `Syndromes grippaux (1985 - en cours)` (renommé incidence RDD 3.csv dans notre dossier data)
 - la gastro `Diarrhée aigue (1991 - en cours)` (renommé incidence RDD 6.csv dans notre dossier data)
 - la varicelle `Varicelle (1991 - en cours)` (renommé incidence RDD 7.csv dans notre dossier data)
 
 Il faut ensuite récupérer le csv pour la France métropolitaine, vous pouvez sélectionné votre région grâce à la colonne `geo_name` (à modifier dans la fonction `epidemies` du script `processing.py`)

## Données sur les fêtes religieuses

Elles sont accessibles par l'url suivant: https://www.calendrier-des-religions.ch/fetes.php

On ne peut pas les télécharger directement donc il est nécessaire de les scrapper. Il suffit de faire tourner le script suivant pour les récupérer: 
```
python script_preprocess/religionscrap.py
```