import pandas as pd
import statsmodels.api as sm
import argparse
import numpy as np

def main(df, window_size):
    """
    Rolling Regression on les indexes avec la date de fin de la période
    """
    X = df[["reel", "effectif", "annee_scolaire"]].dropna().sort_index()

    X["month"] = X.index.to_series().dt.month
    X["weekday"] = X.index.to_series().dt.weekday

    X = X[X.weekday != 2]
    Y = X[["reel"]]

    # Get the dummies for the weekdays
    # X = pd.concat([pd.get_dummies(X["weekday"], prefix="weekday", drop_first=True), X], axis=1)
    X = pd.concat([pd.get_dummies(X["weekday"], prefix="weekday", drop_first=True), X], axis=1)

    #X["weekday_0"] = X["weekday_0"] * X["effectif"]
    X["weekday_1"] = X["weekday_1"] * X["effectif"]
    # X["weekday_2"] = X["weekday_2"] #* X["effectif"]
    X["weekday_3"] = X["weekday_3"] * X["effectif"]
    X["weekday_4"] = X["weekday_4"] * X["effectif"]

    # Drop non used in model
    X.drop("reel", axis=1, inplace=True)
    X.drop("weekday", axis=1, inplace=True)
    X.drop("month", axis=1, inplace=True)
    X.drop("annee_scolaire", axis=1, inplace=True)

    def fit_ols(Y, X):
        mod = sm.OLS(Y, X)
        res = mod.fit()

        return res

    WINDOW_SIZE = window_size
    rolling_res = []
    rolling_X_Y = []
    DROP_LAST = 2 + WINDOW_SIZE
    for n in range(len(X) - DROP_LAST):
        N_START = n
        N_END = n + WINDOW_SIZE
        X_, Y_ = X.iloc[N_START:N_END], Y.iloc[N_START:N_END]

        res = fit_ols(Y_, X_)
        rolling_res.append(res)
        rolling_X_Y.append((X_, Y_))

    rolling_params = pd.DataFrame([r.params.values.tolist() + [r.rsquared] for r in rolling_res])
    rolling_params.columns = X.columns.tolist() + ["rsquared"]
    rolling_params.index = X.index[DROP_LAST:len(X)]


    rolling_pvalues = pd.DataFrame([r.pvalues.values.tolist() for r in rolling_res])
    rolling_pvalues.columns = X.columns.tolist()
    rolling_pvalues.index = X.index[DROP_LAST:len(X)]


    return rolling_res, rolling_X_Y, rolling_params, rolling_pvalues



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--granularite",
                        help="le type de modélisation: au global, par quartier ou par établissement",
                        default = "global",
                        type = str)
    parser.add_argument("--lieu",
                        help="l'endroit que vous souhaitez selectionner",
                        default = "global",
                        type = str)
    parser.add_argument("--seuil",
                        help="seuil de rejet des valeurs aberrantes (en valeurs absolues)",
                        default=1.64,
                        type = float)
    parser.add_argument("--fenetre_temp",
                        help="fenetre temporelle glissante sur laquelle on fit les modèles",
                        default = 360,
                        type = int)


    args = parser.parse_args()

    data = pd.read_pickle("data_processed/complete_data_per_school.pk")
    data_global = pd.read_pickle("data_processed/global.pk")

    col_relative_date = ["nos", "ind", "greves_manquantes", "menu", "ferie", "veille_ferie", "retour_ferie", "vacances",
                         "retour_vacances", "veille_vacances", "inc_grippe", "inc_gastro", "inc_varicelle",
                         "fete_musulmane", "ramadan", "fete_chretienne","fete_juive", "jour", "semaine", "mois",
                         "annee_scolaire", "repas_noel", "porc", "viande","bio", "poisson"]

    if args.granularite == "quartier":
        df = data[data["Quartier"] == args.lieu].reset_index().groupby("date")[
            ["prevision", "reel", "effectif"]].sum().join(
            data_global[col_relative_date])
    elif args.granularite == "etablissement":
        df = data[data["nom_etab"] == args.lieu].reset_index().groupby("date")[
            ["prevision", "reel", "effectif"]].sum().join(
            data_global[col_relative_date])
    else:
        df = data_global

    df["frac"] = df["reel"] / df["effectif"]
    df["reel_moyen_annee"] = df.groupby("annee_scolaire").reel.transform(np.mean)
    df["reel_std_annee"] = df.groupby("annee_scolaire").reel.transform(np.std)

    print(df.shape)
    print(len(df[df.reel == 0]), "jours avec le réel à zéro")
    df = df[df.reel != 0]
    print(len(df[df["jour"] == "Mercredi"]), "jours étant des mercredi")
    df = df[df["jour"] != "Mercredi"]
    print(df.shape)

    df["z_year_score"] = (df.reel - df.reel_moyen_annee) / df.reel_std_annee

    df_origin = df.copy(deep=True)
    df = df_origin[abs(df_origin.z_year_score) < args.seuil].copy()
    print(df.shape)

    #Modèle simple pour le moment
    rolling_res, rolling_X_Y, rolling_param, rolling_pval = main(df=df, window_size=args.fenetre_temp)

    if args.granularite == "quartier":
        rolling_param.to_pickle("results/rolling/" + args.granularite + "/rolling_params_"+args.granularite+"_" + args.lieu + "_" + str(args.fenetre_temp) + ".pk")
        rolling_pval.to_pickle("results/rolling/" + args.granularite + "/rolling_pval_"+args.granularite+"_" + args.lieu + "_" + str(args.fenetre_temp) + ".pk")

    elif args.granularite == "etablissement":
        rolling_param.to_pickle("results/rolling/" + args.granularite + "/rolling_params_"+args.granularite+"_" + args.lieu.split(" ")[0] + "_" + str(args.fenetre_temp) + ".pk")
        rolling_pval.to_pickle("results/rolling/" + args.granularite + "/rolling_pval_"+args.granularite+"_" + args.lieu.split(" ")[0] + "_" + str(args.fenetre_temp) + ".pk")
    else:
        rolling_pval.to_pickle("results/rolling/rolling_params_"+args.granularite+"_" + args.lieu + "_" + str(args.fenetre_temp) + ".pk")
        rolling_pval.to_pickle("results/rolling/rolling_pval_"+args.granularite+"_" + args.lieu + "_" + str(args.fenetre_temp) + ".pk")