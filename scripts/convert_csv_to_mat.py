import pandas as pd
import numpy as np
from scipy.io import savemat
import os
import sys

def csv_to_mat(csv_path, mat_path):
    # Lire le CSV
    df = pd.read_csv(csv_path)

    # Conversion du temps de microsecondes à secondes
    times = df['Tmu'] / 1e6

    # Description des événements (électrode)
    descriptions = df['Electrode']

    # Construire la structure pour Brainstorm
    events = {
        'onsets': np.array(times),
        'descriptions': np.array(descriptions, dtype=np.object_)
    }

    # Créer dossier de sortie si besoin
    os.makedirs(os.path.dirname(mat_path), exist_ok=True)

    # Sauvegarder le .mat
    savemat(mat_path, events)
    print(f"Fichier .mat sauvegardé dans : {mat_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python convert_csv_to_mat.py chemin/fichier.csv chemin/sortie.mat")
        sys.exit(1)
    csv_to_mat(sys.argv[1], sys.argv[2])
