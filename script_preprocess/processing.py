
import datetime
import numpy as np
import pandas as pd
import os



def check_same_value_or_nan(l):
    """Vérifie si 2 fois la même valeur
       ou valeur et np.nan dans liste à deux éléments"""
    if type(l[0]) == float:
        l = [x for x in l if not np.isnan(x)]
    try:
        assert len(set(l)) in [0, 1]
        return True
    except:
        # print(len(set(l)))
        return False


def get_rid_of_nan(l):
    """Keep only the non np.nan value"""
    return [x for x in l if not np.isnan(x)]


def format_name(row):
    # On gère le cas ALAIN FOURNIER E avec le type M/E en premier
    cas_particulier = ["ALAIN FOURNIER E", "MAURICE MACE M"]
    if (row["site_nom"] in cas_particulier) & (row["site_type"] == "M/E"):
        return row["site_nom"][:-1] + "M/E"
    if row["site_nom"][-2:] in ["M.", "E."]:
        return row["site_nom"][:-1]
    elif row["site_nom"][-2:] in [" M", " E", "/E"]:
        return row["site_nom"]
    else:
        return row["site_nom"] + " " + row["site_type"]



def match_etab(liste_etab, liste_effectif):
    dic_match = {}
    for nom in liste_etab:
        # if nom.startswith("EMILE PEHANT"):
        #    print(nom)
        if "M/E" in nom:
            if "/" in nom[:-4]:
                dic_match[nom] = [etab for etab in liste_effectif if
                                  (nom[:-4].split("/")[0] in etab) or (nom[:-4].split("/")[1] in etab)]
            else:
                dic_match[nom] = [etab for etab in liste_effectif if nom[:-4] in etab]
        else:
            dic_match[nom] = [etab for etab in liste_effectif if nom in etab]

    # On traite le cas particulier de JEAN ZAY M à part
    dic_match["JEAN ZAY M"] = ["JEAN ZAY I MATERNELLE", "JEAN ZAY II MATERNELLE"]
    dic_match["MARSAUDERIES E"] = ["MARSAUDERIES ELEMENTAIRE", 'MARSAUDERIES bilingue "Français/Breton"']

    return dic_match



def get_annee_scolaire(date):
    if date.month < 8:
        return str(date.year - 1) + "-" + str(date.year)
    else:
        return str(date.year) + "-" + str(date.year + 1)


def get_effectifs_from_ecoles(row, dic_eff):
    res = []
    annee_scolaire = row["annee_scolaire"]
    for ecole in row["ecole_list"]:
        try:
            effectif = dic_eff[(ecole, annee_scolaire)]
        except:
            effectif = np.nan
        finally:
            res.append(effectif)
    return res


def fromisocalendar(y, w, d):
    return datetime.datetime.strptime("%04dW%02d-%d" % (y, w - 1, d), "%YW%W-%w")

def get_time_range(row):
    if pd.isnull(row["date_de_fin"]):
        return [row["date_de_debut"]]
    else:
        return list(pd.date_range(row["date_de_debut"], row["date_de_fin"]))



def format_epidemie(data, nom):
    df_data = data.reset_index()[["date", "inc"]].sort_values("date")

    # On crée un dictionnaire qui à chaque date associe l'indice épidémique correspondant
    dic = {}
    for i in range(len(df_data) - 1):
        for d in pd.date_range(df_data["date"].iloc[i], df_data["date"].iloc[i + 1]):
            dic[d] = df_data["inc"].iloc[i]

    df = pd.DataFrame([dic.keys(), dic.values()]).transpose()
    df = df.rename(columns={0: "date", 1: "inc" + "_" + nom})

    return df.set_index("date")

def format_religion(data, nom_religion):

    dic_mois = {"Janvier ": "-01-", "Février ": "-02-", "Mars ": "-03-", "Avril ": "-04-", "Mai ": "-05-",
                "Juin ": "-06-", "Juillet ": "-07-", "Août ": "-08-", "Septembre ": "-09-", "Octobre ": "-10-",
                "Novembre ": "-11-", "Décembre ": "-12-"}


    data["jour"] = data[0].apply(lambda x: x.split(" ")[1])
    data["mois"] = data[1].apply(lambda x: x.replace(x.split("2")[0], dic_mois[x.split("2")[0]]))
    data["date"] = data["jour"] + data["mois"]
    data["date"] = data["date"].apply(lambda x: datetime.datetime.strptime(x, "%d-%m-%Y"))
    data["fete_"+nom_religion] = 1

    return data[["date", "fete_"+nom_religion ]].drop_duplicates()


def match_frequentation_effectif(path_data="data", csv_frequentation="frequentation_cantines_v3.csv", csv_effectif ="Effectifs_ecoles.csv"):


    path_frequentation = os.path.join(path_data, csv_frequentation)
    path_effectif = os.path.join(path_data, csv_effectif)

    df_effectif = pd.read_csv(path_effectif)
    df_effectif.columns = df_effectif.columns.str.lower().str.replace(" ", "_").str.replace("é", "e")

    df_frequentation = pd.read_csv(path_frequentation)

    ##################
    # Filtrage des foyers
    ##################

    liste_foyers = [
        "STALINGRAD (Foyer Manu)",
        "STALINGRAD/FOYER MANU",
        "STALINGRAD/FOYER MANU(dépannage )",
        "FOYER CLOS TORREAU (dépannage)",
        "FOYER MANU (dépannage)"
    ]

    df_frequentation = df_frequentation[~df_frequentation.site_nom.isin(liste_foyers)]

    ##################
    # Noms des établissements
    ##################

    # Correction nom des établissements

    dic_site_nom = {}
    for name in df_frequentation["site_nom"].unique():
        if name == "CHENE DARON":
            dic_site_nom[name] = "CHENE D'ARON"
        elif name == "COTE DOR":
            dic_site_nom[name] = "COTE D'OR"
        elif name == "GEORGES SAND":
            dic_site_nom[name] = "GEORGE SAND"
        elif name == "LE BAUT":
            dic_site_nom[name] = "BAUT"
        else:
            dic_site_nom[name] = name

    df_frequentation["site_nom"] = df_frequentation["site_nom"].apply(lambda x: dic_site_nom[x])
    df_frequentation[
        "idx_prev_reel"] = df_frequentation.site_nom + " - " + df_frequentation.site_type + " - " + df_frequentation.date
    df_frequentation["idx"] = range(len(df_frequentation))

    #print("shape data 1", df_frequentation.shape)


    ##################
    # Check sur les identifiants
    ##################

    # Groupby ce qui devrait être un identifiant
    idx_counts = df_frequentation.groupby("idx_prev_reel").idx.agg(list)
    # On regarde les id site_nom + site_type + date présents plus d'une fois
    l_idx_2 = idx_counts[(idx_counts.map(len) > 1)].tolist()
    # On récupère les listes d'index
    l_idx_2 = [i for s in l_idx_2 for i in s]

    #######################################################
    # Doublons : Au moins un de (prevision, reel) renseigné
    # EN FAIT : on remarque que dans ce cas, c'est toujours l'un ou l'autre
    # + pour toute ligne avec prévision et sans réel,
    # il existe le demi jumeau avec réel sans prévision

    # On crée les lignes avec les deux valeurs
    #######################################################

    # On garde uniquement les lignes avec les indexes sélectionnés
    tmp = df_frequentation[df_frequentation.idx.isin(l_idx_2)]
    # On garde finalement uniquement les lignes avec l'un ou l'autre de renseigné
    tmp = tmp[~((tmp.prevision.isnull()) & (tmp.reel.isnull()))]

    # Toutes les valeurs
    tmp = tmp.groupby(["idx_prev_reel"]).agg(list)


    #print("Check up : toutes les listes sont [same_value, same_value] ou [value, np.nan]")
    #print(tmp.drop(["site_id", "site_nom_sal", "reel_s", "prevision_s", "idx"], axis=1).applymap(
    #    check_same_value_or_nan).sum(axis=0))



    # Filter out the nan
    tmp[["prevision", "reel"]] = tmp[["prevision", "reel"]].applymap(get_rid_of_nan)

    # Check longueur des listes obtenues
    #print(tmp[["prevision", "reel"]].applymap(len).sum())

    # On prend seulement le premier élément
    tmp[["prevision", "reel"]] = tmp[["prevision", "reel"]].applymap(lambda x: x[0])

    # On prend le premier élément (on a vérifié que c'était deux fois le même)
    for col in ['site_type', 'date', 'site_nom']:
        tmp[col] = tmp[col].map(lambda x: x[0])

    SELECTED_COLS = ["date", "prevision", "reel", "site_nom", "site_type"]

    l_df = []
    l_df.append(tmp[SELECTED_COLS].copy(deep=True))

    #######################################################
    # Doublons : Aucun de réel et prévision renseigné
    # On garde une seule ligne parmi les deux
    #######################################################

    tmp = df_frequentation[df_frequentation.idx.isin(l_idx_2)]
    tmp = tmp[((tmp.prevision.isnull()) & (tmp.reel.isnull()))]
    tmp = tmp.drop("idx", axis=1).drop_duplicates()[SELECTED_COLS]

    l_df.append(tmp.copy(deep=True))

    #assert all(l_df[0].columns == l_df[1].columns)
    #assert len(l_idx_2) == 2 * sum([len(x) for x in l_df])

    #######################################################
    # 1 ligne par identifiant direct
    #######################################################

    l_idx_1 = idx_counts[(idx_counts.map(len) == 1)].tolist()
    l_idx_1 = [i for s in l_idx_1 for i in s]

    tmp = df_frequentation[df_frequentation.idx.isin(l_idx_1)]

    l_df.append(tmp[SELECTED_COLS].copy(deep=True))

    # Concat
    df_frequentation = pd.concat(l_df, axis=0).reset_index(drop=True)

    #######################################################
    # MERGE sur les effectifs
    #######################################################

    #print("shape data 2", df_frequentation.shape)


    df_frequentation["nom_etab"] = df_frequentation.apply(format_name, axis=1)

    # Noms uniques dans chaque dataframe
    nom_etab_unique_frequentation = df_frequentation.nom_etab.unique()
    nom_etab_unique_effectif = df_effectif.ecole.unique()

    # Matching nom_frequentation (nom_etab) -> list:noms_effectifs (ecole)
    d_match_nom_etab = match_etab(nom_etab_unique_frequentation, nom_etab_unique_effectif)

    df_frequentation["ecole_list"] = df_frequentation.nom_etab.map(lambda key: d_match_nom_etab[key])

    #On change la date au format datetime pour pouvoir trouver l'annee scolaire
    df_frequentation["date"] = pd.to_datetime(df_frequentation.date)
    df_frequentation['annee_scolaire'] = df_frequentation.date.map(get_annee_scolaire)

    d_effectif_by_ecole_annee_scolaire = df_effectif.set_index(["ecole", "annee_scolaire"])["effectif"].to_dict()

    df_frequentation["effectif_list"] = df_frequentation.apply(
        lambda x: get_effectifs_from_ecoles(x, d_effectif_by_ecole_annee_scolaire), axis=1)

    df_frequentation["effectif"] = df_frequentation["effectif_list"].map(lambda l: np.nansum(l))

    df_frequentation.to_pickle("data_processed/frequentation_effectif.pk")


def feries(path_data = "data", csv_feries = "jours-feries-seuls.csv"):

    path_dfg = os.path.join(path_data, csv_feries)
    df_ferie = pd.read_csv(path_dfg)

    df_ferie["date"] = df_ferie["date"].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
    df_ferie["ferie"] = 1

    df_veille_ferie = df_ferie["date"].apply(lambda x: x - datetime.timedelta(days=1)).to_frame()
    df_veille_ferie["veille_ferie"] = 1

    df_retour_ferie = df_ferie["date"].apply(lambda x: x + datetime.timedelta(days=1)).to_frame()
    df_retour_ferie["retour_ferie"] = 1

    df_fer_comp = pd.concat([df_ferie, df_retour_ferie, df_veille_ferie]).fillna(0)
    #print(df_fer_comp.shape)

    df_fer_comp.set_index("date")[["ferie", "veille_ferie", "retour_ferie"]].to_pickle("data_processed/feries.pk")


def epidemies(path_data="data", csv_grippe="incidence RDD 3.csv", csv_gastro="incidence RDD 6.csv", csv_varicelle="incidence RDD 7.csv"):

    path_grippe = os.path.join(path_data, csv_grippe)
    path_gastro = os.path.join(path_data, csv_gastro)
    path_varicelle = os.path.join(path_data, csv_varicelle)
    grippe = pd.read_csv(path_grippe, sep=',', engine="python")
    gastro = pd.read_csv(path_gastro, sep=',', engine="python")
    varicelle = pd.read_csv(path_varicelle, sep=',', engine="python")


    grippe["date"] = [fromisocalendar(int(str(t)[0:4]), int(str(t)[4:6]), 1) for t in grippe["week"]]
    grippe.index = pd.to_datetime(grippe['date'])
    grippe = grippe.drop('date', axis=1)
    grippe = grippe[grippe["geo_name"] == "PAYS-DE-LA-LOIRE"]

    gastro["date"] = [fromisocalendar(int(str(t)[0:4]), int(str(t)[4:6]), 1) for t in gastro["week"]]
    gastro.index = pd.to_datetime(gastro['date'])
    gastro = gastro.drop('date', axis=1)
    gastro = gastro[gastro["geo_name"] == "PAYS-DE-LA-LOIRE"]

    varicelle["date"] = [fromisocalendar(int(str(t)[0:4]), int(str(t)[4:6]), 1) for t in varicelle["week"]]
    varicelle.index = pd.to_datetime(varicelle['date'])
    varicelle = varicelle.drop('date', axis=1)
    varicelle = varicelle[varicelle["geo_name"] == "PAYS-DE-LA-LOIRE"]

    df_grippe = format_epidemie(grippe, "grippe")
    df_gastro = format_epidemie(gastro, "gastro")
    df_varicelle = format_epidemie(varicelle, "varicelle")

    df_epidemies = df_grippe.join(df_gastro).join(df_varicelle)

    df_epidemies.fillna(0).to_pickle("data_processed/epidemies.pk")



def greves(path_data="data", csv_greve_ville="Journees_de_greve.csv", csv_greve_sncf="mouvements-sociaux-depuis-2002.csv", excel_greve_supp="missing_strikes.xlsx"):

    ##################
    # Fichier grèves Nantes Métropole
    ##################


    path_dfg = os.path.join(path_data, csv_greve_ville)
    dfg = pd.read_csv(path_dfg)
    dfg.columns = ["date", "ind"]
    dfg["date"] = pd.to_datetime(dfg["date"])

    ##################
    # Fichier grèves de la SNCF
    ##################
    path_csvms = os.path.join(path_data, csv_greve_sncf)
    dfms = pd.read_csv(path_csvms, encoding='utf-8', sep=';')

    dfms["nos"] = dfms.organisations_syndicales.map(lambda x: len(x.split(";")))

    dfms["date_de_debut"] = pd.to_datetime(dfms["date_de_debut"])
    dfms["date_de_fin"] = pd.to_datetime(dfms["date_de_fin"])


    dfms["time_range"] = dfms.apply(get_time_range, axis=1)

    new_rows = []
    for idx, row in dfms.iterrows():
        for date in row["time_range"]:
            # print(date)
            row_ = row.copy()
            row_["date"] = date
            new_rows.append(row_)

    dfms = pd.DataFrame(new_rows)

    """Comme on a plusieurs mouvements enregistrés pour une seule date,
    on les rassemble en faisant une moyenne du taux de grevistes et sdu nombre d'organisations syndicales"""

    dfms_clean = dfms.groupby("date")[["taux_grevistes", "nos"]].mean()

    """On s'assure que les dates soient uniques: une observation par date"""
    assert len(dfms_clean) == len(dfms["date"].unique())



    ##################
    # Fichier grèves construit à la main correspondant à des grèves non référencées dans les
    # deux fichiers ci-dessus
    ##################

    path_hm = os.path.join(path_data, excel_greve_supp)
    dhm = pd.read_excel(path_hm)

    dfg.set_index("date", inplace=True)
    dhm.set_index("date", inplace=True)

    dfms_clean.join(dfg, how="outer")[["ind", "nos", "taux_grevistes"]].join(dhm, how ="outer").to_pickle("data_processed/greves.pk")


def menus(path_data="data", csv_menus_1="menus_2011-2015.csv", csv_menus_2="menus_2016-2019.csv"):

    path_df = os.path.join(path_data, csv_menus_1)
    df2011 = pd.read_csv(path_df, encoding='latin')
    df2011["date"] = df2011["date"].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))
    df2011 = df2011[["date", "menu"]].groupby("date").agg(list)


    path_df = os.path.join(path_data, csv_menus_2)
    df2016 = pd.read_csv(path_df, encoding='utf-8')
    df2016["Date"] = df2016["Date"].apply(lambda x: datetime.datetime.strptime(x, '%d/%m/%Y'))
    df2016.columns = ["date", "rang", 'menu']
    df2016 = df2016[["date", "menu"]].groupby("date").agg(list)

    df = pd.concat([df2011, df2016])

    df.to_pickle("data_processed/menus.pk")


def religions(path_data="data", csv_fetes_musulmanes="fetes_musulmanes.csv", csv_ramadan="ramadan.csv", csv_fetes_chretiennes="fetes_chretiennes.csv", csv_fetes_juives="fetes_juives.csv"  ):

    path_m = os.path.join(path_data, csv_fetes_musulmanes)
    data_m = pd.read_csv(path_m, encoding = "ISO-8859-1", header = None)

    data_m[0] = data_m[0].apply(lambda x: x.replace(" ", "") if " " in x else x)
    data_m["date"] = data_m[0].apply(lambda x: datetime.datetime.strptime(x, "%d/%m/%Y"))
    data_m["fete_musulmane"] = 1


    path_r = os.path.join(path_data, csv_ramadan)
    data_r = pd.read_csv(path_r, encoding = "ISO-8859-1")
    data_r["date"] = data_r["date"].apply(lambda x: datetime.datetime.strptime(x, "%d/%m/%Y"))

    data_mus = data_m[["date", "fete_musulmane"]].merge(data_r, on="date", how="outer")[
        ["date", "fete_musulmane", "ramadan"]].fillna(0)

    path_c = os.path.join(path_data, csv_fetes_chretiennes)
    data_c = pd.read_csv(path_c, encoding="ISO-8859-1", header=None)
    data_c = format_religion(data_c, "chretienne")

    path_j = os.path.join(path_data, csv_fetes_juives)
    data_j = pd.read_csv(path_j, encoding="ISO-8859-1", header=None)
    data_j = format_religion(data_j, "juive")

    data_religion = data_mus.merge(data_c, how="outer").merge(data_j, how="outer").fillna(0)

    data_religion.set_index("date").to_pickle("data_processed/religions.pk")


def vacances(path_data="data", csv_vacances="vacances_Nantes_2011-2019.csv"):

    path_dfg = os.path.join(path_data, csv_vacances)
    df_vacances = pd.read_csv(path_dfg, encoding = "ISO-8859-1").drop("Unnamed: 0", axis = 1)

    df_vacances = df_vacances[df_vacances["Source"] == "Registre manuel"]

    df_veille_vac = df_vacances["date_start"].apply(
        lambda x: datetime.datetime.strptime(x, "%Y-%m-%d") - datetime.timedelta(days=1)).to_frame().rename(
        columns={"date_start": "date"})
    df_veille_vac["veille_vacances"] = 1

    df_retour_vac = df_vacances["date_end"].apply(
        lambda x: datetime.datetime.strptime(x, "%Y-%m-%d") + datetime.timedelta(days=1)).to_frame().rename(
        columns={"date_end": "date"})
    df_retour_vac["retour_vacances"] = 1

    df_vac = pd.concat([pd.DataFrame(
        pd.date_range(df_vacances["date_start"].iloc[i], df_vacances["date_end"].iloc[i])).rename(
        columns={0: "date"}) for i in range(len(df_vacances))])
    df_vac["vacances"] = 1

    df_vac_complet = pd.concat([df_vac, df_retour_vac, df_veille_vac])


    df_vac_complet.set_index("date").to_pickle("data_processed/vacances.pk")


