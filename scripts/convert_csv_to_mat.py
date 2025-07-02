"""
convert_csv_to_mat.py

Ce script convertit un fichier .csv d'événements (extrait d'annotations EEG, comme des décharges épileptiformes interictales) 
en un fichier .mat compatible avec Brainstorm. Il extrait les temps d'occurrence des événements (colonne 'Tmu') et les étiquettes
de canal (colonne 'Electrode').

Les temps sont convertis de microsecondes en secondes et sauvegardés dans un dictionnaire contenant :
- 'onsets' : vecteur numpy de temps (en secondes)
- 'descriptions' : vecteur numpy de chaînes de caractères (nom de canal associé)

---------------------
🔧 Utilisation (en ligne de commande) :
python convert_csv_to_mat.py chemin/vers/fichier.csv chemin/vers/sortie.mat

💡 Exemple :
python convert_csv_to_mat.py C:/Users/boyer/github/ECOFEC/data/raw/csv_file/f29d_19ICA_FINAL.csv C:/Users/boyer/github/ECOFEC/data/raw/mat_file/f29d_19ICA_FINAL.mat
---------------------

Format attendu du fichier .csv : colonnes 'Tmu' (en µs) et 'Electrode'
"""

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
