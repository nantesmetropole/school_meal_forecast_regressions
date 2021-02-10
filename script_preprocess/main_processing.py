import subprocess
import os
from processing import match_frequentation_effectif, feries, epidemies, greves, menus, religions, vacances
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--path_data",
                        help="nom du dossier contenant les fichiers de données",
                        default="data",
                        type=str)
    parser.add_argument("--frequentation",
                        help="données de fréquentation",
                        default = "frequentation_cantines_v3.csv",
                        type=str)
    parser.add_argument("--effectif",
                        help="données d'effectif",
                        default= "Effectifs_ecoles.csv",
                        type=str)
    parser.add_argument("--feries",
                        help="données sur les jours fériés",
                        default= "jours-feries-seuls.csv",
                        type=str)
    parser.add_argument("--grippe",
                        help="données sur la grippe",
                        default= "incidence RDD 3.csv",
                        type=str)
    parser.add_argument("--gastro",
                        help="données sur la gastro",
                        default="incidence RDD 6.csv",
                        type=str)
    parser.add_argument("--varicelle",
                        help="données sur la varicelle",
                        default="incidence RDD 7.csv",
                        type=str)
    parser.add_argument("--greves_ville",
                        help="données sur les grèves spécifiques à la métropole",
                        default="Journees_de_greve.csv",
                        type=str)
    parser.add_argument("--greves_sncf",
                        help="données sur les grèves SNCF",
                        default="mouvements-sociaux-depuis-2002.csv",
                        type=str)
    parser.add_argument("--greves_autre",
                        help="données sur des grèves autres",
                        default="missing_strikes.xlsx",
                        type=str)
    parser.add_argument("--menus_1",
                        help="données sur les menus",
                        default="menus_2011-2015.csv",
                        type=str)
    parser.add_argument("--menus_2",
                        help="données sur les menus (autre format)",
                        default="menus_2016-2019.csv",
                        type=str)
    parser.add_argument("--fetes_musulmanes",
                        help="données sur les fetes musulmanes",
                        default="fetes_musulmanes.csv",
                        type=str)
    parser.add_argument("--ramadan",
                        help="données sur le ramadan",
                        default="ramadan.csv",
                        type=str)
    parser.add_argument("--fetes_chretiennes",
                        help="données sur les fetes chretiennes",
                        default="fetes_chretiennes.csv",
                        type=str)
    parser.add_argument("--fetes_juives",
                        help="données sur les fetes juives",
                        default="fetes_juives.csv",
                        type=str)
    parser.add_argument("--vacances",
                        help="données sur les vacances de la métropole",
                        default="vacances_Nantes_2011-2019.csv",
                        type=str)


    args = parser.parse_args()



    match_frequentation_effectif(path_data=args.path_data, csv_frequentation=args.frequentation,
                                 csv_effectif=args.effectif)

    feries(path_data=args.path_data, csv_feries=args.feries)

    epidemies(path_data=args.path_data, csv_grippe=args.grippe, csv_gastro=args.gastro, csv_varicelle=args.varicelle)

    greves(path_data=args.path_data, csv_greve_ville=args.greves_ville, csv_greve_sncf=args.greves_sncf, excel_greve_supp=args.greves_autre)

    menus(path_data=args.path_data, csv_menus_1=args.menus_1, csv_menus_2=args.menus_2)

    religions(path_data=args.path_data, csv_fetes_musulmanes=args.fetes_musulmanes, csv_ramadan=args.ramadan, csv_fetes_chretiennes=args.fetes_chretiennes, csv_fetes_juives=args.fetes_juives )

    vacances(path_data=args.path_data, csv_vacances=args.vacances)
















