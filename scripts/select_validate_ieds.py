import numpy as np
import pandas as pd
import mne
import os
import yaml
from scipy.io import savemat
import matplotlib.pyplot as plt  # Importation manquante pour matplotlib

# Charger le fichier de configuration YAML
with open('C:/Users/boyer/github/ECOFEC/data/config/d3bd_ied_selection.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Lire les chemins des fichiers depuis la configuration
csv_file = config['csv_file']
edf_file = config['edf_file']
text_file_path = config['text_file_path']

# Charger le fichier CSV
df_csv = pd.read_csv(csv_file)

# Charger le fichier EDF
raw_edf = mne.io.read_raw_edf(edf_file, preload=True)

# Sélectionner les canaux souhaités
channels = config['channels']
raw_edf.pick_channels(channels)

# Ordre des électrodes 
ordre_electrodes = config['ordre_electrodes']

# Convertir la colonne 'Tmu' de microsecondes en secondes
df_csv['Tmu_seconds'] = df_csv['Tmu'] / 1e6

# Fonction pour définir les périodes
def definir_periodes(df, periodes):
    df['periode'] = None
    for periode in periodes:
        start = periode['start']
        end = periode['end'] if periode['end'] != 'max' else df['Tmu_seconds'].max()
        mask = (df['Tmu_seconds'] >= start) & (df['Tmu_seconds'] <= end)
        df.loc[mask, 'periode'] = periode['name']
    return df

# Appliquer la définition des périodes
df_csv = definir_periodes(df_csv, config['periodes'])

# Fonction pour calculer les occurrences et les ratios par période
def calculer_occurrences_et_ratios(df):
    ratios = {}
    periodes = df['periode'].unique()
    for periode in periodes:
        df_periode = df[df['periode'] == periode]
        occurrences = df_periode['Electrode'].value_counts()
        total_occurrences = occurrences.sum()
        ratios[periode] = (occurrences / total_occurrences) * 100
    return ratios

# Calculer les occurrences et les ratios
ratios_par_periode = calculer_occurrences_et_ratios(df_csv)

# Afficher les ratios en pourcentage pour vérifier
for periode, ratios in ratios_par_periode.items():
    print(f"Ratios pour la période {periode}:")
    print(ratios.round(0))  # Arrondir à deux décimales

def valider_evenements_selectionnes(raw, selection, n_target_dict, periode=None):
    """
    Valide manuellement les événements sélectionnés et assure que le nombre d'événements par électrode 
    atteigne la cible spécifiée dans `n_target_dict`, tout en respectant l'ordre des électrodes.
    
    :param raw: Données brutes EEG
    :param selection: DataFrame des événements sélectionnés
    :param n_target_dict: Dictionnaire avec le nombre cible d'événements pour chaque électrode
    :param periode: Période à filtrer ('Eveil' ou 'Sommeil'), None pour inclure toutes les périodes
    :return: DataFrame avec les événements validés
    """
    validation = []
    event_count = {electrode: 0 for electrode in n_target_dict}  # Compteur d'événements par électrode
    idx = 0  # Initialisation de l'index

    # Filtrer par période si spécifié
    if periode:
        selection = selection[selection['periode'] == periode]

    # Extraire les électrodes dans l'ordre de n_target_dict
    electrodes_ordered = list(n_target_dict.keys())
    
    # Parcourir les électrodes dans l'ordre du dictionnaire
    for electrode in electrodes_ordered:
        # Sélectionner les événements pour cette électrode
        selection_electrode = selection[selection['Electrode'] == electrode]
        
        # Appliquer la validation pour chaque événement de cette électrode
        for idx, row in selection_electrode.iterrows():
            if event_count[electrode] < n_target_dict[electrode]:
                event_time = row['Tmu_seconds']
                event_periode = row['periode']
                start = max(0, event_time - 0.5)
                end = min(raw.times[-1], event_time + 0.5)

                # Visualisation du signal autour de l'événement
                fig = raw.plot(start=start, duration=1.0, show=False)

                # Ajouter un titre avec l'électrode concernée et ajuster la position
                plt.title(f"Événement {idx} - Électrode {electrode} - Période: {event_periode} à {event_time:.3f}s", pad=20)
                plt.show()

                # Validation manuelle
                valid = input(f"Valider cet événement pour l'électrode {electrode} (Période : {event_periode}) ? (y/n) : ").strip().lower()
                if valid == 'y':
                    validation.append(row)
                    event_count[electrode] += 1  # Incrémenter le compteur pour l'électrode
                    print(f"Événement validé pour l'électrode {electrode}. Total validé: {event_count[electrode]}")
                else:
                    print(f"Événement rejeté pour l'électrode {electrode}.")
        
        # Arrêter dès qu'on a atteint le nombre cible pour cette électrode
        if event_count[electrode] >= n_target_dict[electrode]:
            print(f"Nombre cible d'événements atteint pour l'électrode {electrode}.")

    print("Validation terminée.")
    return pd.DataFrame(validation)

# Exemple d'utilisation
n_target_dict = {
    'C4': 5,
    'C3': 2,
    'T4-F8': 1,
    'T4/F8': 1, 
    'T4': 1
}

# Spécifier la période : 'Eveil' ou 'Sommeil'
periode_selectionnee = input("Sélectionner la période ('Eveil' ou 'Sommeil') ou appuyer sur Entrée pour toutes les périodes : ").strip()

# Appel de la fonction avec df_csv
validated_events = valider_evenements_selectionnes(raw_edf, df_csv, n_target_dict, periode_selectionnee)

# Affichage du résultat des événements validés
print("Événements validés :")
print(validated_events)

# Fonction pour enregistrer les événements sélectionnés dans un fichier .mat et un fichier texte
def enregistrer_evenements(validated_events, config, mat_filename_base, txt_filename_base, ratios_par_periode):
    """
    Enregistre les événements validés dans un fichier .mat et un fichier texte, en incluant les ratios par période.

    :param validated_events: DataFrame des événements validés
    :param config: Dictionnaire de configuration chargé depuis le fichier YAML
    :param mat_filename_base: Nom de base pour le fichier .mat
    :param txt_filename_base: Nom de base pour le fichier texte
    :param ratios_par_periode: Dictionnaire des ratios calculés pour chaque période
    """
    # Récupérer le chemin de sauvegarde depuis la configuration
    save_folder = config['save_folder']

    # Filtrer les événements par période (Eveil, Sommeil)
    periodes_valides = validated_events['periode'].unique()

    for periode in periodes_valides:
        if periode in ['Eveil', 'Sommeil']:  # Nous nous intéressons seulement aux périodes "Eveil" et "Sommeil"

            # Créer le nom du fichier .mat
            mat_filename_period = mat_filename_base.replace(".mat", f"_{periode}.mat")
            mat_filepath = os.path.join(save_folder, mat_filename_period)

            # Créer le nom du fichier texte
            txt_filename_period = txt_filename_base.replace(".txt", f"_{periode}.txt")
            txt_filepath = os.path.join(save_folder, txt_filename_period)

            # Filtrer les événements pour la période courante
            events_periode = validated_events[validated_events['periode'] == periode]

            # Enregistrement dans un fichier .mat
            event_times = events_periode['Tmu_seconds'].values
            electrodes = events_periode['Electrode'].values

            # Utiliser la fonction fournie pour le format .mat
            sauvegarder_evenements_mat(event_times, electrodes, mat_filepath)
            print(f"Événements enregistrés dans le fichier .mat : {mat_filepath}")

            # Enregistrement dans un fichier texte
            with open(txt_filepath, 'w') as f:
                # Écrire les en-têtes
                f.write("Electrode, Tmu_seconds, Periode, Ratio\n")

                # Ajouter les événements et leurs ratios
                for _, row in events_periode.iterrows():
                    # Extraire le ratio correspondant à l'électrode pour cette période
                    ratio = ratios_par_periode.get(periode, {}).get(row['Electrode'], 0)
                    f.write(f"{row['Electrode']}, {row['Tmu_seconds']:.6f}, {row['periode']}, {ratio:.2f}\n")
            
            print(f"Événements enregistrés dans le fichier texte : {txt_filepath}")

# Fonction pour enregistrer les occurrences dans un fichier .mat (structure adaptée)
def sauvegarder_evenements_mat(event_times, electrodes, mat_file_path):
    """
    Enregistre les événements dans un fichier .mat avec la structure spécifiée.

    :param event_times: Liste des timestamps des événements
    :param electrodes: Liste des électrodes associées aux événements
    :param mat_file_path: Chemin complet pour enregistrer le fichier .mat
    """
    events = {
        'onsets': np.array(event_times),
        'descriptions': np.array(electrodes, dtype=np.object_)  # Conversion en objet pour le format MATLAB
    }
    savemat(mat_file_path, events)

# Exemple d'utilisation après validation des événements
mat_filename_base = "evenements_valides.mat"  
txt_filename_base = "evenements_valides_avec_ratios.txt"

# Sauvegarder les événements validés dans les fichiers avec les ratios pour "Eveil" et "Sommeil"
enregistrer_evenements(validated_events, config, mat_filename_base, txt_filename_base, ratios_par_periode)
