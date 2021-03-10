import os
import datetime
import json
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import numpy as np
import warnings
import statsmodels.api as sm
warnings.filterwarnings('ignore')


def create_df_quartier(data, data_global, columns_from_global, quartier):
    """Cette fonction crée et renvoie la dataframe contenant toutes les observations pour un quartier."""
    df = (
        data[data["Quartier_detail"] == quartier]
            # Pour pouvoir ensuite grouper sur la date, on la retire de l'index
            .reset_index()
            .groupby("date")[["prevision", "reel", "effectif"]]
            .sum()
            # On enrichit avec les variables exogènes
            .join(data_global[columns_from_global])
    )
    return df


def create_df_etab(data, data_global, columns_from_global, etab):
    """Cette fonction crée et renvoie la dataframe contenant toutes les observations pour un établissement."""

    df = (
        data[data["nom_etab"] == etab]
            # Pour pouvoir ensuite grouper sur la date, on la retire de l'index
            .reset_index()
            .groupby("date")[["prevision", "reel", "effectif"]]
            .sum()
            # On enrichit avec les variables exogènes
            .join(data_global[columns_from_global])
    )
    return df


def create_df_global(data, data_global, columns_from_global):
    """Cette fonction crée et renvoie la dataframe contenant la somme des observations sur tous les établissements."""
    df = (
        data.reset_index()
            .groupby("date")[["prevision", "reel", "effectif"]]
            .sum()
            # On enrichit avec les variables exogènes
            .join(data_global[columns_from_global])
    )
    return df


def delete_rows_null_reel(df):
    """Cette fonction renvoie une dataframe débarassée des observations avec un réel nul."""
    return df[df.reel != 0]


def delete_rows_wednesday(df):
    """Cette fonction renvoie une dataframe débarassée des observations des mercredis."""
    return df[df["jour"] != "Mercredi"]


def select_columns(df, selected_columns):
    """Cette fonction permet de sélectionner seulement certaines colonnes"""
    return df[selected_columns]


def create_month_columns(X):
    """Cette fonction permet de créer les dummies * effectif pour les mois"""
    # On crée des dummies pour chaque jour
    X_month = pd.get_dummies(X.index.to_series().dt.month, drop_first=True, prefix="month")
    for col in X_month:
        X_month[col] = X_month[col] * X["effectif"]
    X_month.index = X.index
    X = pd.concat([X_month, X], axis=1)
    return X


def create_day_with_fish_columns(X):
    """Cette fonction permet de créer les dummies variables * effectif : jour_avec/sans_poisson
       Pour les lundis, mardis et jeudis."""

    # On crée des dummies pour chaque jour
    X = pd.concat([pd.get_dummies(X["jour"]), X], axis=1)

    # Produits de : dummy jour / dummy poisson et effectif
    for day in ["Lundi", "Mardi", "Jeudi"]:
        X[day + "_avec_poisson"] = X[day] * X["poisson"] * X["effectif"]
        X[day + "_sans_poisson"] = X[day] * X["poisson"].apply(lambda x: 1 - x) * X["effectif"]

    # Supprimer colonnes non utilisées
    for col in ["jour", "Vendredi", "Lundi", "Mardi", "Jeudi", "poisson"]:
        X.drop(col, axis=1, inplace=True)

    return X


def create_repas_noel_column(X):
    """Crée la variable pour le repas de Noël"""
    X["repas_noel"] = X["repas_noel"] * X["effectif"]
    return X


def fit_ols(Y, X):
    """Fit OLS model to both Y and X"""
    model = sm.OLS(Y, X)
    model = model.fit()
    return model


def get_output_model(X, Y, df, model, alpha):
    """Renvoie la dataframe X_pred avec toutes les prédictions out of sample"""

    X_pred = X

    # Predictions classiques
    pred = model.predict(X_pred)
    # Prediction avec intervalle de confiance
    predictions = model.get_prediction(X_pred)
    X_pred["pred_upper"] = predictions.summary_frame(alpha=alpha)["obs_ci_upper"]

    X_pred = X_pred.join(df[["prevision", "reel"]])
    X_pred["pred"] = pred
    X_pred["gaspillage"] = (X_pred["prevision"] - X_pred["reel"]) / X_pred["prevision"]
    X_pred["gaspi_pred"] = (X_pred.pred - X_pred.reel) / X_pred.pred
    X_pred["gaspi_pred_upper"] = (X_pred.pred_upper - X_pred.reel) / X_pred.pred_upper

    return X_pred


def log_gaspillage(X_pred):
    """Affiche les métriques relatives au gaspillage out of sample"""

    print("gaspillage réel", X_pred.gaspillage.mean())
    print("gaspillage avec nos prédictions - upper", X_pred.gaspi_pred_upper.mean())

    print(
        len(X_pred[X_pred.gaspillage < 0]),
        "reel : jours avec un gaspillage négatif / un manque de repas",
    )

    print(
        len(X_pred[X_pred.gaspi_pred < 0]),
        "pred  : jours avec un gaspillage négatif / un manque de repas",
    )

    print(
        len(X_pred[X_pred.gaspi_pred_upper < 0]),
        "pred upper : jours avec un gaspillage négatif / un manque de repas",
    )

    print("\n\n")


def store_results(name, model, X_pred, z_year_score_threshold, alpha):
    """Enregistre modèle, paramètres et prédictions out of sample"""
    # Info communes au nom des 2 fichiers
    info_model = f"{name}_{z_year_score_threshold}_{1-alpha}"
    params = model.params.to_dict()

    # Modèle complet
    path_pickle = f"results/general/model_{info_model}.pk"
    with open(path_pickle, "wb") as f:
        pickle.dump(model, f)

    # Modèle : seulement les paramètres
    path_json = f"results/general/params_{info_model}.json"
    with open(path_json, "w") as f:
        json.dump(params, f)

    # DataFrame prédiction out of sample
    path_pickle = f"results/general/x_pred_{info_model}.pk"
    X_pred.to_pickle(path_pickle)


def main(etab, quartier, z_year_score_threshold, alpha, start_training_date, begin_date, end_date, verbose=False):
    """Constitution du dataset / fit du modèle / prediction out of sample"""

    columns_from_global = [
        "nos",
        "ind",
        "greves_manquantes",
        "menu",
        "ferie",
        "veille_ferie",
        "retour_ferie",
        "vacances",
        "retour_vacances",
        "veille_vacances",
        "inc_grippe",
        "inc_gastro",
        "inc_varicelle",
        "fete_musulmane",
        "ramadan",
        "fete_chretienne",
        "fete_juive",
        "jour",
        "semaine",
        "mois",
        "annee_scolaire",
        "repas_noel",
        "porc",
        "viande",
        "bio",
        "poisson",
        "4_derniers_jours",
    ]

    columns_for_model = [
        "reel",
        "effectif",
        "z_year_score",
        #"jour",
        "repas_noel",
        "poisson",
        "viande",
        "4_derniers_jours",
    ]

    path_data = "data_processed"

    filename_data_per_school = "complete_data_per_school.pk"  # Données de repas / effectifs par école
    filename_data_global = "global.pk"  # Données exogènes pour enrichissements
    path_data_per_school = os.path.join(path_data, filename_data_per_school)
    path_data_global = os.path.join(path_data, filename_data_global)

    data = pd.read_pickle(path_data_per_school)
    data_global = pd.read_pickle(path_data_global)

    ## Récupérations des données
    if (etab is None) & (quartier is None):
        df = create_df_global(data, data_global, columns_from_global)
        type_ = "global"
        name = "global"
    elif etab is not None:
        df = create_df_etab(data=data, data_global=data_global, columns_from_global=columns_from_global, etab=etab)
        type_ = "etab"
        name = etab
    elif quartier is not None:
        df = create_df_quartier(data=data, data_global=data_global, columns_from_global=columns_from_global,
                                quartier=quartier)
        type_ = "quartier"
        name = quartier

    if verbose:
        print(df.shape[0], "lignes", type_, ":", name)
        print(f"date_min : {df.index.min().date()}", f"\ndate_max : {df.index.max().date()}")

    ## Suppression lignes réel nulles et mercredi
    df = delete_rows_null_reel(df=df)
    df = delete_rows_wednesday(df=df)

    # Calcul du z_year_score et censure
    if verbose:
        print(df.shape[0], "lignes avant censure par le z_year_score")

    df["z_year_score"] = (df.reel - df.groupby("annee_scolaire").transform(np.mean).reel) / df.groupby(
        "annee_scolaire").transform(np.std).reel
    # df = df[df.z_year_score.map(np.abs) < z_year_score_threshold]

    if verbose:
        print(df.shape[0], "lignes après censure par le z_year_score")

    df = select_columns(df=df, selected_columns=columns_for_model + ["prevision"])

    # Création des dummies et Sélection sur le z_year_score
    X = df.dropna().drop("prevision", axis=1)
    #X = create_day_with_fish_columns(X=X)
    X["poisson"] = X["poisson"] * X["effectif"]
    X["viande"] = X["viande"] * X["effectif"]

    X = create_month_columns(X)
    X = create_repas_noel_column(X=X)

    print("X columns", X.columns)

    # on enlève quatre derniers jours de l'années des mois de juin et/ou juillet pour éviter les colinéarités
    X["month_6"] = X["month_6"] * X["4_derniers_jours"].apply(lambda x: 1 - x)
    X["month_7"] = X["month_7"] * X["4_derniers_jours"].apply(lambda x: 1 - x)

    # 4 derniers jours
    X["4_derniers_jours"] = X["4_derniers_jours"] * X["effectif"]

    # X et Y pour modélisation (on garde le z_year_score pour faire la censure sur le train mais pas sur le test)
    Y = X[["reel", "z_year_score"]].sort_index()
    X = X.drop(["reel"], axis=1).sort_index()

    # Date de début et de fin du train
    start_training_date = datetime.datetime.strptime(start_training_date, "%Y-%m-%d")
    begin_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    # Sélection du train
    X_train, Y_train = X[(X.index > start_training_date) & (X.index <= begin_date)], Y[
        (Y.index > start_training_date) & (Y.index <= begin_date)]
    # Censure grâce au z_year score
    X_train, Y_train = X_train[X_train.z_year_score.map(np.abs) < z_year_score_threshold], Y_train[
        Y_train.z_year_score.map(np.abs) < z_year_score_threshold]
    # On enlève la colonne z_year_score
    X_train, Y_train = X_train.drop(["z_year_score"], axis=1), Y_train.drop(["z_year_score"], axis=1)

    # Le test est toute la portion après le train jusqu'à la date de fin
    X, Y = X.drop(["z_year_score"], axis=1), Y.drop(["z_year_score"], axis=1)
    X_test, Y_test = X[(begin_date < X.index) & (X.index <= end_date)], Y[
        (begin_date < Y.index) & (Y.index <= end_date)]

    #print("columns X", X_train.columns)
    #print("types", X_train.dtypes)
    model = fit_ols(Y_train, X_train)

    X_pred = get_output_model(X_test, Y_test, df, model, alpha=alpha)

    if verbose:
        X_pred[["pred", "reel"]].plot()
        plt.show()

    return model, X_pred