import os
import pandas as pd
import spacy
from sklearn.feature_extraction.text import CountVectorizer
import datetime
import numpy as np


from processing import get_annee_scolaire


if __name__ == "__main__":

    #print("files", os.listdir("data_processed"))

    ##########################
    # Chargement des données
    ##########################

    path_g = os.path.join("data_processed", "greves.pk")
    g = pd.read_pickle(path_g)
    g["ind"] = g.ind.map(lambda x: 1 if x == "GREVE" else 0)
    g = g[["taux_grevistes", "nos", "ind", "greves_manquantes"]]

    path_m = os.path.join("data_processed", "menus.pk")
    m = pd.read_pickle(path_m)

    path_fe = os.path.join("data_processed", "frequentation_effectif.pk")
    fe = pd.read_pickle(path_fe)

    path_ferie = os.path.join("data_processed", "feries.pk")
    feries = pd.read_pickle(path_ferie)

    path_vacs = os.path.join("data_processed", "vacances.pk")
    vacances = pd.read_pickle(path_vacs)

    path_epidemies = os.path.join("data_processed", "epidemies.pk")
    epidemies = pd.read_pickle(path_epidemies)

    path_religions = os.path.join("data_processed", "religions.pk")
    religions = pd.read_pickle(path_religions)

    ##########################
    # Join sur les dates des différentes BDD
    ##########################


    df = fe.groupby("date")[["prevision", "reel", "effectif"]].sum().join(g).join(m).join(feries).join(vacances).join(epidemies).join(religions)

    ##########################
    # Remplacement des valeurs manquantes
    ##########################

    for col in df.isnull().sum()[df.isnull().sum()>0].index.drop("menu"):
        df[col] = df[col].fillna(0)
    df["menu"] = df["menu"].map(lambda x: x if type(x) == list else [])

    ####################################
    # Ajout des jours, mois semaines, année scolaire, repas noel
    ####################################
    dic_jour = {0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi", 4: "Vendredi", 5: "Samedi", 6: "Dimanche"}
    dic_mois = {1: "Janvier", 2: "Fevrier", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin", 7: "Juillet", 8: "Aout",
                9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Decembre"}

    df["jour"] = df.index.weekday
    df["jour"] = df["jour"].apply(lambda x: dic_jour[x])
    df["semaine"] = df.index.week
    df["mois"] = df.index.month
    df["mois"] = df["mois"].apply(lambda x: dic_mois[x])
    df["annee_scolaire"] = df.index.to_series().map(get_annee_scolaire)

    date_repas_noel = ["2012-12-20", "2013-12-19", "2014-12-18", "2015-12-17", "2016-12-15",
                       "2017-12-21", "2018-12-20"]
    l_noel = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in date_repas_noel]

    df_noel = pd.DataFrame(l_noel, columns=["date"])
    df_noel["repas_noel"] = 1
    df = df.join(df_noel.set_index("date"))
    df["repas_noel"] = df["repas_noel"].fillna(0)

    ####################################
    # Ajout du gaspillage
    ####################################

    assert df.isnull().sum().sum() == 0

    df["gaspillage_volume"] = df["prevision"] - df["reel"]
    df["gaspillage_pourcentage"] = 100 * (df["prevision"] - df["reel"]) / df["prevision"]


    ####################################
    # Ajout des variables liées au menu
    ####################################

    nlp = spacy.load("fr_core_news_sm")
    corpus = df['menu'].apply(lambda x: "".join([i + " " for i in x]))
    corpus = corpus.dropna()

    # stop_word
    liste = ['04', '10', '17', '18225', '2015', '2016', '220gr', '268', '29', '500', '500g', '5kg', '850''500', '500g',
             '5kg', '850', 'ab', 'an', 'au', 'aux', 'avec', 'baut', 'bbc', 'de', 'des', 'du', 'en', 'et', 'gr', 'kg',
             'la', 'le', 'les', 'ou', 'par', 's17', 'sa', 'sans', 'ses', 'son']


    # Create CountVectorizer object
    vectorizer = CountVectorizer(strip_accents='ascii', stop_words=liste, lowercase=True, ngram_range=(1, 1))

    # Generate matrix of word vectors
    bow_matrix = vectorizer.fit_transform(corpus)

    # Convert bow_matrix into a DataFrame
    bow_df = pd.DataFrame(bow_matrix.toarray())

    # Map the column names to vocabulary
    bow_df.columns = vectorizer.get_feature_names()
    bow_df.index = df.index

    # feature porc
    l_porc = ["carbonara", "carbonata", "cassoulet", "chipo", "chipolatas", "choucroute",
              "cordon", "croziflette", "francfort", "jambon", "knacks", "lardons", "porc", "rosette",
              "saucisse", "saucisses", "tartiflette"]

    df["porc"] = sum([bow_df[alim] for alim in l_porc])
    df['porc'] = df['porc'] > 0
    df['porc'] = df['porc'].astype('int')

    # feature viande
    l_viande = ["roti", "agneau", "blanquette", "boeuf", "boudin", "boulettes",
                "bourguignon", "bourguignonne", "canard", "carne", "chapon", "colombo",
                "couscous", "dinde", "escalope", "farci", "foie", "kebab", "lapin", "merguez",
                "mouton", "napolitaines", "nuggets", "paupiette", "pintade",
                "poulet", "steak", "stogonoff", "strogonoff", "tagine", "tajine",
                "veau", "viande", "volaile", "volaille", "carbonara", "carbonata", "cassoulet", "chipo", "chipolatas",
                "choucroute",  "cordon", "croziflette", "francfort", "jambon", "knacks", "lardons", "porc", "rosette",
                "saucisse", "saucisses", "tartiflette", "parmentier"]

    df["viande"] = sum([bow_df[alim] for alim in l_viande])
    df['viande'] = df['viande'] > 0
    df['viande'] = df['viande'].astype('int')

    df = df.reset_index().rename(columns = {"index":"date"})


    l_index = ["2018-01-22", "2017-10-09", "2017-05-09", "2016-10-18", "2016-04-25", "2015-05-26", "2014-11-24",
             "2014-05-26", "2014-03-31", "2014-01-20", "2012-01-16", "2012-01-30", "2012-07-02", "2012-10-01",
             "2011-01-17", "2011-01-31", "2011-09-13", "2015-06-22", "2015-01-19", "2014-06-30", "2012-06-18",
             "2011-06-20"]
    index = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in l_index]


    for i in index:
        df.loc[df[df["date"] == i].index, "viande"] = 1

    # traitement particulier des lasagnes napolitaines pour éviter les confusions avec les lasagnes de poisson
    l_index = ["2016-02-22", "2016-02-04", "2015-11-23", "2015-11-17", "2015-10-05",
             "2015-05-04", "2015-01-26", "2014-12-15", "2013-09-23", "2012-10-09", "2012-05-21", "2012-02-27",
             "2011-11-03", "2011-09-05", "2011-05-09", "2012-12-10", "2013-12-02", "2014-05-12", "2016-05-09"]
    index = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in l_index]

    for i in index:
        df.loc[df[df["date"] == i].index, "viande"] = 1

    # traitement particulier de certains termes qui peuvent être utilisés pour du poisson ou de la viande sautés, chili, pot au feu, bolognaise, courgette farcie,ravioli
    l_index = ["2016-01-28", "2016-03-17", "2016-03-07", "2015-09-15", "2012-12-06", "2012-05-03", "2012-02-09",
             "2011-11-03",
             "2011-09-13", "2011-06-07", "2011-04-04", "2014-06-12", "2012-11-12", "2015-06-22"]
    index = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in l_index]

    for i in index:
        df.loc[df[df["date"] == i].index, "viande"] = 1

    # traitement particulier pour parmentier végétale, steack de soja
    l_index = ["2019-11-25", "2014-06-20"]
    index = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in l_index]

    for i in index:
        df.loc[df[df["date"] == i].index, "viande"] = 0


    # feature poisson
    l_poisson = ["poissons", "sardines", "perray", "thon", "calamar", "lieu", "colin", "crabe", "crevette", "crustace",
                 "dorade", "maquereau", "poisson", "rillette", "sardine", "saumon"]

    df["poisson"] = sum([bow_df[alim] for alim in l_poisson])
    df['poisson'] = df['poisson'] > 0
    df['poisson'] = df['poisson'].astype('int')
    df['poisson'][(df['viande'] == 1) & (df['poisson'] == 1)] = np.zeros(
        len(df['poisson'][(df['viande'] == 1) & (df['poisson'] == 1)]))

    # traitement particulier parmentier poisson #nuggets de poisson,steack de soja et sale au thon, carbo de saumon
    l_index = ["2019-05-17", "2019-05-17", "2019-02-01", "2018-11-23", "2018-10-19", "2018-09-14", "2018-06-05",
             "2018-03-27", "2018-01-16", "2017-12-01", "2017-09-22", "2017-05-05", "2016-05-03", "2016-02-26",
             "2016-01-15", "2015-11-20", "2015-09-22", "2015-09-08", "2015-06-05", "2014-09-08", "2014-03-25",
             "2014-02-18", "2014-01-24", "2013-12-10", "2013-11-29", "2013-10-01", "2012-12-14", "2012-10-19",
             "2012-09-21", "2012-03-16", "2012-01-20", "2011-09-09", "2011-03-18", "2019-03-08"]
    index = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in l_index]


    for i in index:
        df.loc[df[df["date"] == i].index, "viande"] = 0
        df.loc[df[df["date"] == i].index, "poisson"] = 1

    # traitement particulier paella de la mer, filet

    l_index = ['2011-01-10', '2012-01-09', '2011-01-07', "2012-01-06"]
    index = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in l_index]

    for i in index:
        df.loc[df[df["date"] == i].index, "poisson"] = 1

    # 2 menus : végé et viande, on considère que c'est un menu végé
    l_index = ["2015-11-13", "2015-09-11"]
    index = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in l_index]

    for i in index:
        df.loc[df[df["date"] == i].index, "poisson"] = 0
        df.loc[df[df["date"] == i].index, "viande"] = 0

    # 2 menus : poisson et viande, on considère que c'est un menu poisson
    l_index = ["2015-11-20", "2015-10-16", "2015-10-02", "2015-09-25", "2015-09-18", "2015-09-04", "2015-06-25",
             "2015-06-11"]
    index = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in l_index]

    for i in index:
        df.loc[df[df["date"] == i].index, "poisson"] = 1
        df.loc[df[df["date"] == i].index, "viande"] = 0

    # menu inconnu, mais probablement avec viande d'après le modèle
    df.loc[df[df["date"] == datetime.datetime.strptime("2015-10-15", "%Y-%m-%d")].index, "viande"] = 1

    # feature bio
    df['bio'] = bow_df["bio"]

    # set date as index
    df = df.set_index("date")

    ###############################################################
    # Ajout des 4 premiers et 4 derniers jours de l'année scolaire (grosse incertitude)
    #############################################################

    ind = []
    temp = []
    subset = df.copy()

    #print("subset", subset["annee_scolaire"].unique()[1:])

    for i in range(1, 5):

        for annee in subset["annee_scolaire"].unique()[1:]:
            temp.append(min(subset[(subset.index.year == min(subset[subset["annee_scolaire"] == annee].index.year)) & (
                        subset["annee_scolaire"] == annee)].index))
            df.loc[temp, "4_premiers_jours"] = 1
            ind.append(temp)

            subset.drop(temp, inplace=True)
            temp = []

    for i in range(1, 5):

        for annee in subset["annee_scolaire"].unique()[:-1]:
            temp.append(max(subset[(subset.index.year == max(subset[subset["annee_scolaire"] == annee].index.year)) & (
                        subset["annee_scolaire"] == annee)].index))
            df.loc[temp, "4_derniers_jours"] = 1
            ind.append(temp)

            subset.drop(temp, inplace=True)
            temp = []
    df["4_derniers_jours"].fillna(0, inplace=True)
    df["4_premiers_jours"].fillna(0, inplace=True)




    ####################################
    # Tests (longueur et valeurs manquantes)
    ####################################

    assert len(df) == 1188

    df.to_pickle("data_processed/global.pk")
    df.to_excel("data_processed/global.xlsx")


