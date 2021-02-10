import argparse
from general_model import main, store_results


if __name__ == "__main__":

    parser = argparse.ArgumentParser()


    parser.add_argument("--seuil",
                        help="seuil de rejet des valeurs aberrantes (en valeurs absolues)",
                        default=1.64,
                        type=float)
    parser.add_argument("--int_conf",
                        help="intervalle de confiance pour les prédictions (0.9 = IC à 90%)",
                        default= 0.9,
                        type=float)
    parser.add_argument("--start_training_date",
                        help="date à laquelle on commence à prendre les observations dans le jeu de données d'entrainement",
                        default= "2013-09-01",
                        type=str)
    parser.add_argument("--begin_date",
                        help="date à partir de laquelle on cherche à prédire",
                        default="2018-09-01",
                        type=str)
    parser.add_argument("--end_date",
                        help="date de fin de la prédiction",
                        default= "2019-09-01",
                        type=str)

    args = parser.parse_args()

    model_global, X_pred_global = main(etab=None, quartier=None, z_year_score_threshold=args.seuil,
                                       alpha=(1 - args.int_conf), start_training_date=args.start_training_date, begin_date=args.begin_date,
                                       end_date=args.end_date)

    store_results(name="global", model=model_global, X_pred=X_pred_global,
                  z_year_score_threshold=args.seuil, alpha=(1 - args.int_conf))




