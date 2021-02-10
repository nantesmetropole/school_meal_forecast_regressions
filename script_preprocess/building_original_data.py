import os
import pandas as pd

if __name__ == "__main__":

    print("files", os.listdir("data_processed"))

    ##########################
    # Chargement des données global
    ##########################

    path_g = os.path.join("data_processed", "greves.pk")
    g = pd.read_pickle(path_g)
    g["ind"] = g.ind.map(lambda x: 1 if x == "GREVE" else 0)
    g = g[["taux_grevistes", "nos", "ind", "greves_manquantes"]]

    path_m = os.path.join("data_processed", "menus.pk")
    m = pd.read_pickle(path_m)

    path_ferie = os.path.join("data_processed", "feries.pk")
    feries = pd.read_pickle(path_ferie)

    path_vacs = os.path.join("data_processed", "vacances.pk")
    vacances = pd.read_pickle(path_vacs)

    path_epidemies = os.path.join("data_processed", "epidemies.pk")
    epidemies = pd.read_pickle(path_epidemies)

    path_religions = os.path.join("data_processed", "religions.pk")
    religions = pd.read_pickle(path_religions)

    df_global = g.join(m, how="outer").join(feries, how="outer").join(vacances, how="outer")\
        .join(epidemies, how="outer").join(religions, how="outer")

    ####################################
    # Ajout des jours, mois semaines
    ####################################
    dic_jour = {0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi", 4: "Vendredi", 5: "Samedi", 6: "Dimanche"}
    dic_mois = {1: "Janvier", 2: "Fevrier", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin", 7: "Juillet", 8: "Aout",
                9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Decembre"}

    df_global["jour"] = df_global.index.weekday
    df_global["jour"] = df_global["jour"].apply(lambda x: dic_jour[x])
    df_global["semaine"] = df_global.index.week
    df_global["mois"] = df_global.index.month
    df_global["mois"] = df_global["mois"].apply(lambda x: dic_mois[x])

    ####################################
    # Remplacement des valeurs manquantes
    ####################################

    for col in df_global.isnull().sum()[df_global.isnull().sum()>0].index.drop("menu"):
        df_global[col] = df_global[col].fillna(0)
    df_global["menu"] = df_global["menu"].map(lambda x: x if type(x) == list else [])


    ##########################
    # Chargement des données par etablissement
    ##########################

    path_fe = os.path.join("data_processed", "frequentation_effectif.pk")
    fe = pd.read_pickle(path_fe)

    ##########################
    # Construction d'un indice unique par observation
    ##########################

    fe["idx_prev_reel"] = fe.site_nom + " - " + fe.site_type + " - " + fe.date.apply(lambda x: str(x))

    assert len(fe["idx_prev_reel"].unique()) == 104095


    ##########################
    # Ajout de données complementaires
    ##########################


    path_immo = os.path.join("data", "Liste ETS_geo_AE12102020.xlsx")
    immo = pd.read_excel(path_immo)
    assert len(immo) == 93

    path_orga = os.path.join("data", "orga_des_etablissements.xlsx")
    orga = pd.read_excel(path_orga).rename(columns={"etab": "nom_etab"})
    assert len(orga) == 89

    path_etab = os.path.join("data", "code_etablissement.csv")
    code_etab = pd.read_csv(path_etab, sep=";")
    assert len(code_etab)== 169

    ##########################
    # Assemblage de toutes les données
    ##########################

    df = fe.merge(immo, how = "left").merge(orga, on = "nom_etab", how = "left").merge(code_etab[["Appellation officielle", "Code établissement"]], on = "Appellation officielle", how = "left").set_index("date").join(df_global)

    ####################################
    # Modification des noms des établissements et quartiers
    ####################################
    df["nom_etab"] = df["nom_etab"].apply(lambda x: x.lower().replace(" ", "_").replace("/", "_") if "/" in x else x.lower().replace(" ", "_"))


    assert len(df) == 104095


    df.to_pickle("data_processed/complete_data_per_school.pk")


