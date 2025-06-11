import numpy as np
import pandas as pd
import mne
import os
import yaml
from scipy.io import savemat
import matplotlib
matplotlib.use('Qt5Agg')  # Forcer le backend Qt5 interactif
import matplotlib.pyplot as plt


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

# Fonction pour transformer les ratios en nombre d’occurrences à valider
def generer_n_target_dict(ratios_par_periode, periode_selectionnee, n_total):
    """
    Génère un dictionnaire avec le nombre d'événements à sélectionner par électrode
    en fonction des ratios et du nombre total souhaité.

    :param ratios_par_periode: dictionnaire des ratios calculés par période
    :param periode_selectionnee: période à considérer ('Eveil', 'Sommeil', etc.)
    :param n_total: nombre total d'événements à sélectionner
    :return: dictionnaire {électrode: n_occurrences}
    """
    if periode_selectionnee not in ratios_par_periode:
        raise ValueError(f"La période '{periode_selectionnee}' n'existe pas dans les ratios calculés.")

    ratios = ratios_par_periode[periode_selectionnee]
    n_target_dict = (ratios / 100 * n_total).round().astype(int)

    # S'assurer que la somme soit exactement égale à n_total (ajustement si besoin)
    diff = n_total - n_target_dict.sum()
    if diff != 0:
        # Trier par ratio décroissant pour prioriser les plus fréquents
        sorted_electrodes = ratios.sort_values(ascending=False).index
        for electrode in sorted_electrodes:
            n_target_dict[electrode] += np.sign(diff)
            diff -= np.sign(diff)
            if diff == 0:
                break

    return n_target_dict.to_dict()

def valider_evenements_selectionnes(raw, selection, n_target_dict, periode=None):
    validation = []
    event_count = {electrode: 0 for electrode in n_target_dict}

    if periode:
        selection = selection[selection['periode'] == periode]

    electrodes_ordered = list(n_target_dict.keys())

    for electrode in electrodes_ordered:
        selection_electrode = selection[selection['Electrode'] == electrode]
        selection_electrode = selection_electrode.sort_values('Tmu_seconds')

        for idx, row in selection_electrode.iterrows():
            if event_count[electrode] >= n_target_dict[electrode]:
                break

            event_time = row['Tmu_seconds']
            start = max(0, event_time - 0.5)
            end = min(raw.times[-1], event_time + 0.5)

            fig = raw.plot(start=start, duration=1.0, show=False)
            plt.title(f"Électrode {electrode} · {row['periode']} @ {event_time:.3f}s", pad=20)
            plt.show()

            valid = input(f"Valider cet événement ? (y/n/exit) : ").strip().lower()
            if valid == 'exit':
                print("Validation interrompue par l'utilisateur.")
                return pd.DataFrame(validation)
            elif valid == 'y':
                validation.append(row)
                event_count[electrode] += 1
                print(f"✅ Validé ({event_count[electrode]}/{n_target_dict[electrode]} pour {electrode})")
            else:
                print("❌ Rejeté")

        print(f"➡️  Électrode {electrode} terminée : {event_count[electrode]}/{n_target_dict[electrode]} validés.\n")

    print("✅ Validation terminée pour toutes les électrodes.")
    return pd.DataFrame(validation)

# Spécifier la période : 'Eveil' ou 'Sommeil'
periode_selectionnee = input("Sélectionner la période ('Eveil' ou 'Sommeil') ou appuyer sur Entrée pour toutes les périodes : ").strip()

# Définir le nombre total d’événements à sélectionner
n_total_evenements = int(input("Nombre total d'événements à valider pour cette période : ").strip())

n_target_dict = generer_n_target_dict(ratios_par_periode, periode_selectionnee, n_total_evenements)

# ➕ Affichage du dictionnaire pour vérification
print(f"\n🎯 Nombre d'événements à valider pour chaque électrode ({periode_selectionnee}) :")
for electrode, n in n_target_dict.items():
    print(f"  - {electrode} : {n}")

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
