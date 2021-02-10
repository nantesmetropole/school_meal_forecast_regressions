import pandas as pd
import statsmodels.api as sm
import argparse
import numpy as np

def main(df, window_size):
    """
    Rolling Regression on les indexes avec la date de fin de la période
    """

    X = df[["reel", "effectif", "annee_scolaire", "mois", "jour", "repas_noel", "poisson"]].dropna().sort_index()

    """Mois"""
    X = pd.concat(
        [
            pd.get_dummies(X["mois"]),
            X,
        ],
        axis=1,
    )
    X.drop("mois", axis=1, inplace=True)
    #print("columns", X.columns)
    X.drop("Juillet", axis=1, inplace=True)

    """Jour"""
    X = pd.concat(
        [
            pd.get_dummies(X["jour"]),
            X,
        ],
        axis=1,
    )
    X.drop("jour", axis=1, inplace=True)
    X.drop("Vendredi", axis=1, inplace = True)

    # Tuesday, Thursday, Friday (Monday is reference, Wednesday is excluded)
    for day in ["Lundi", "Mardi", "Jeudi"]:
        X[day + "_avec_poisson"] = (
                X[day] * X["poisson"] * X["effectif"]
        )
        X[day + "_sans_poisson"] = (
                X[day] * X["poisson"].apply(lambda x: 1 - x)* X["effectif"]
        )
    # Will drop weekday, and weekday_{} for all
    X.drop("Lundi", axis=1, inplace = True)
    X.drop("Mardi", axis=1, inplace = True)
    X.drop("Jeudi", axis=1, inplace = True)
    X.drop("poisson", axis=1, inplace=True)

    X["repas_noel"] = X["repas_noel"]*X["effectif"]

    Y = X["reel"]

    # Drop non used in model
    X.drop("reel", axis = 1, inplace = True)
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
    parser.add_argument("seuil", help="seuil de rejet des valeurs aberrantes (en valeurs absolues)", type = float)
    parser.add_argument("fenetre_temp", help="fenetre temporelle glissante sur laquelle on fit les modèles", type = int)


    args = parser.parse_args()

    data = pd.read_pickle("data_processed/complete_data_per_school.pk")
    data_global = pd.read_pickle("data_processed/global.pk")

    col_relative_date = ["nos", "ind", "greves_manquantes", "menu", "ferie", "veille_ferie", "retour_ferie", "vacances",
                         "retour_vacances", "veille_vacances", "inc_grippe", "inc_gastro", "inc_varicelle",
                         "fete_musulmane", "ramadan", "fete_chretienne","fete_juive", "jour", "semaine", "mois",
                         "annee_scolaire", "repas_noel", "porc", "viande","bio", "poisson"]

    '''On remplace le "/" dans nom etab car sinon je ne peux pas enregistrer le fichier'''
    data["nom_etab"] = data["nom_etab"].apply(lambda x: x.replace('/', '-') if "/" in x else x)

    '''On enlève trois établissements pour lesquels l'historique est trop faible pour faire tourner le modèle rolling'''
    for etab in [i for i in set(data["nom_etab"]) if i not in ["emile_pehant_m", "emile_pehant_e", "alain_fournier_m_e"]]:

        print("etab", etab)

        df = data[data["nom_etab"] == etab].reset_index().groupby("date")[
                ["prevision", "reel", "effectif"]].sum().join(
                data_global[col_relative_date])


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


        rolling_param.to_pickle("results/rolling/etablissement/rolling_params_etablissement_" + etab + "_" + str(args.fenetre_temp) + ".pk")
        rolling_pval.to_pickle("results/rolling/etablissement/rolling_pval_etablissement_" + etab + "_" + str(args.fenetre_temp) + ".pk")

