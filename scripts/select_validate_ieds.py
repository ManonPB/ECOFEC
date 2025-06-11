# scripts/select_validate_ieds.py

import yaml
import pandas as pd
import mne
from preprocessing.ied_selection import (
    definir_periodes,
    calculer_occurrences_et_ratios,
    valider_evenements_selectionnes,
    enregistrer_evenements
)

# Charger le fichier de configuration YAML
with open('data/config/d3bd_ied_selection.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Lire les chemins des fichiers depuis la configuration
csv_file = config['csv_file']  # récupère le chemin depuis la config YAML
edf_file = config['edf_file']  # pareil pour EDF

df_csv = pd.read_csv(csv_file)
print("Colonnes dans CSV :", df_csv.columns)


# Charger le fichier CSV des événements
df_csv = pd.read_csv(csv_file)

# Charger le fichier EDF (données EEG brutes)
raw_edf = mne.io.read_raw_edf(edf_file, preload=True)

# Sélectionner les canaux d'intérêt
raw_edf.pick_channels(config['channels'])

# Ajouter la colonne 'periode' au DataFrame en fonction des périodes définies dans config
df_csv, periodes_numeriques = definir_periodes(df_csv, config['periodes'])

# Calculer les occurrences et ratios par période
occurrences, ratios = calculer_occurrences_et_ratios(df_csv, periodes_numeriques)

print("Occurrences par période :", occurrences)
print("Ratios par période :", ratios)

# Sélection manuelle : demander à l'utilisateur la période choisie (ou toutes si vide)
periode_selectionnee = input("Sélectionner la période ('Eveil' ou 'Sommeil') ou appuyer sur Entrée pour toutes les périodes : ").strip()
if periode_selectionnee == "":
    periode_selectionnee = None

# Validation manuelle des événements selon la période choisie et nombre cible
n_target = config.get('n_occurrences', 10)
validated_events = valider_evenements_selectionnes(
    signal=raw_edf.get_data(picks=config['channels'])[0],  # Premier canal sélectionné (exemple)
    events = df_csv[df_csv['periode'] == periode_selectionnee]['Tmu'].values if periode_selectionnee else df_csv['Tmu'].values,
    sampling_rate=raw_edf.info['sfreq'],
    nom_canal=config['channels'][0],
    config=config,
    nb_a_selectionner=n_target
)

# Enregistrer les événements validés (formats .mat et .txt)
enregistrer_evenements(
    evenements_valides=validated_events,
    fichier_sortie=config.get('save_folder', '.') + "/evenements_valides",
    sampling_rate=raw_edf.info['sfreq']
)
