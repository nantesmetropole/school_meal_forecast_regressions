import subprocess
import argparse
import pandas as pd

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("seuil", help="seuil de rejet des valeurs aberrantes (en valeurs absolues)", type = float)
    parser.add_argument("fenetre_temp", help="fenetre temporelle glissante sur laquelle on fit les modèles", type = int)


    args = parser.parse_args()

    data = pd.read_pickle("data_processed/complete_data_per_school.pk")

    for quartier in data["Quartier"].unique():
        print("quartier", quartier)
        subprocess.Popen(["python", "models/rolling_models.py",  "quartier",  quartier, str(args.seuil), str(args.fenetre_temp)])

