# Prédiction de la fréquentation des cantines scolaires de Nantes métropole

Dans le cadre d'un appel à projet de Nantes métropole sur la réduction du gaspillage alimentaire, nous avons réalisé une modélisation de la fréquentation des cantines scolaires de la métropole. 

Nantes métropole nous a mis à disposition les historiques des données de fréquentation des écoles de la métropole sur les 10 dernières années. Nous avons également récupéré d'autres sources de données en open source afin de trouver des varaibles qui pourraient avoir une influence sur la fréquentation des restaurants scolaires. 

## Architecture

Les données sont séparées selon deux dossiers
* les données brutes sont stockées dans le dossier data
* les données affinées sont dans le dossier data_processed

Ensuite, le code est organisé selon 3 dossiers principaux:
* script_preprocess correspond à l'ensemble des scripts permettant de construire les données nécesaires à l'analyse et au focntionnement des modèles
* src recense l'ensemble des notebooks ayant permis l'élaboration des modèles et l'analyse des résultats
* models correspond aux scripts d'automatisation des modèles

Enfin les résultats des modèles sont stockés dans le dossier results.

## Installation

Tout d'abord, vous devez cloner ce dépôt si vous souhaiter reproduire les résultats suivants.

Ensuite, vous pouvez reproduire l'environnemnt de développement python grâce à la commande suivante:
```
pip install -r requirements.txt
```

Enfin, il est nécessaire de télécharger la librairie fr_core_news_sm pour l'analyse de texte avec spacy:

```
python -m spacy download fr_core_news_sm
```


## Fonctionnement


### Assemblage des données

Les données brutes (fréquentation, effectifs, vacances etc) doivent être stockés dans le dossier data et respecté le format précisé dans le document data_preparation.md.

Toutes ces données brutes vont ensuite être processées afin de construire les bases finales pour l'analyse de données et la modélisation. Pour faire ce processing, il suffit de faire tourner le code suivant:

```
python script_preprocess/main_processing.py
```

Les arguments sont mis par défaults avec les données de Nantes métropole:
  - `--path_data`: dossier dans lequel se trouve les données brutes `"data"`
  - `--frequentation`: données de fréquentation au format csv `"frequentation_cantines_v3.csv""`
  - `--effectif`: données relatives aux effectifs des écoles `"Effectifs_ecoles.csv"`
  - `--greves_ville`: données sur les grèves relatives à la métropole `"Journees_de_greve.csv"`
  - `--vacances`: données sur les vacances scolaires relative à la métropole `"vacances_Nantes_2011-2019.csv"`
  
 Ensuite, les menus nous ont été donné via deux fichiers mais vous pouvez en renseigner seulement un:
  - `--menus_1`: données sur les menus entre 2011 et 2015 `"menus_2011-2015.csv"`
  - `--menus_2`: données sur les menus entre 2016 et 2020`"menus_2016-2019.csv"`

A la suite de ce script, les fichiers préprocessés seront stockés dans le dossier data_processed

Afin de construire la base complète (1 date / 1 établissment / 1 effectif / 1 fréquentation prévisionnelle / 1 fréquentation réelle), il suffit d'éxecuter la commande suivante:
```
python script_preprocess/building_original_data.py
```

Une base de données au format pickle "complete_data_per_school.pk" sera automatiquement généré dans le dossier data_processed. 

Ensuite, pour accéder aux données agrégés par date sur l'ensemble des établissments, soit on peut faire un groupby date sur le jeu de données précédent, soit on peut exécuter la commande suivante:

```
python script_preprocess/building_aggregated_data.py
```

Cela va générer la base de données "global.pk" dans le dossier data_processed.

Pour ouvrir ces jeux de données, il est possible d'uiliser la méthode read_pickle de pandas (>=0.20.3).

De plus, vous pouvez trouver plus d'informations sur le preprocessing dans le fichier note_methodologique.pdf

### Modélisation

Nous avons réalisé types de modélisation:
* rolling: on entraine successivement des modèles sur une fenêtre temporelle glissante afin de s'assurer de la robustessse de ces modèles
    * paramètres: granularité, lieu, seuil pour enlever les valeurs aberrantes, intervalle temporel
* général: on entraine un modèle sur les années scolaires 2012-2013 à 2017-2018 et on réalise des prédictions sur l'année 2018-2019
    * paramètres: seuil, intervalle de confiance pour la prédiction, date de début d'entrainement, date de début de prédiction, date de fin de prédiction

Afin de gagner en flexibilité, nous avons ajouté des paramètres pour faire des prédictions à différents niveaux:
* etablissement
* quartier
* global (sur l'ensemble des établissements)

Afin de faire un rolling modèle au global, il suffit de faire tourner la commande suivante

```
python models/rolling_models.py
```
Les arguments sont les suivants:
  - `--granularité`: préciser si vous souhaitez un modèle au global, par quartier ou par établissement (par défault: `"global"`)
  - `--lieu`: préciser le nom de l'entité sur laquelle vous souhaitez une prédiction (par défault: `"global"`)
  - `--seuil`: seuil selon lequel on exclue des valeurs aberrantes (ramené à la distribution d'une loi normale centrée réduite) `1.64`
  - `--fenetre_temp`: nombre d'observations (de jours) sur lesquelles on souhaite calculer la moyenne mobile `360`


Pour faire tourner le modèle global au général, il suffit de réaliser la commande suivante:
```
python models/main_gm_global.py  
```

Enfin, pour réaliser l'ensemble des prédictions par quartiers ou par établissements, nous avons crée des scripts supplémentaires dont le fonctionnement est semblable:
```
python models/main_gm_etablissements.py 
```

Pour ces deux dernières commandes, les arguments sont les suivants:
  - `--seuil`: seuil selon lequel on exclue des valeurs aberrantes (ramené à la distribution d'une loi normale centrée réduite) `1.64`
  - `--int_conf`: intervalle de confiance que l'on souhaite prendre pour ajuster les prédictions (par défault: `0.9`)
  - `--start_training_date`: date à partir de laquelle on prend les observations dans l'échantillon d'apprentissage (par défault: `"2013-09-01"`)
  - `--begin_date`: date à partir de laquelle on prend les observations dans l'échantillon de test (par défault: `"2018-09-01"`)
  - `--end_date`: date finale pour l'échantillon de test  (par défault: `"2019-09-01"`)


### Stockage des résultats

Nous avons créé un dossier `results`dans lequel des sous-dossiers `general` et `rolling` sont présents.  

Pour les modèles de type `général`, nous stockons les 3 outputs suivants:
 - le modèle `model_global_1.64_0.9.pk`pour le modèle au global avec un seuil à 1.64 et un intervalle de confiance à 90%
 - les paramètres du modèle ``params_global_1.64.09.pk`` 
 - les variables explicatives de l'échantillon de test ``x_pred_1.64.09.pk``

Pour les modèles de type `rolling`, nous stockons deux outputs:
- les paramètres du modèle `rolling_params_etablissement_gaston_serpette_m_360.pk` par exemple pour l'établissment `gaston serpette m` avec une fenêtre de 360 observations (3 ans de données à peu près)
- les p-values associés à chaque variable explicative `rolling_pval_etablissement_gaston_serpette_m_360.pk`

### Exploitation des résultats

Nous avons crée deux notebooks pour analyser les résultats de ces différents modèles et surtout pour comparer l'efficacité des modèles en focntion de la granularité.

* 10_model_per_schools pour les résultats par école
* 11_metrics_global_model pour les résultats au global. 

## Licence

Le code lié à ce projet a été développé par Maestria Innovation avec les contributions de Selim Mellouk et Gilles Cornec, pour le compte de Nantes Métropole. Lire le document LICENSE.md pour plus d'informations.