import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import yaml

"""
### ⚠️ Configuration Reminder

Each time you use this script, make sure to update the `.yaml` configuration file:

- **Line 19**: path to the input CSV file (`input_csv`)
- **Line 22**: path to the output folder (`save_folder`)

"""

# Charger le fichier de configuration YAML
with open('C:/Users/boyer/github/ECOFEC/data/config/d3bd_7dcf_event_analysis.yaml', 'r') as f:
    config = yaml.safe_load(f)

yaml_filename_prefix = os.path.splitext(os.path.basename('C:/Users/boyer/github/ECOFEC/data/config/d3bd_7dcf_event_analysis.yaml'))[0][:9]

# Définir les chemins
save_folder = config['save_folder']
os.makedirs(save_folder, exist_ok=True)
csv_file = config['input_csv']  # corriger 'csv_file' → 'input_csv'

# Lire le fichier CSV
df = pd.read_csv(csv_file)

# Supprimer les colonnes spécifiées
df.drop(columns=config['drop_columns'], inplace=True)

# Convertir Tmu en secondes
df['Tmu'] = df['Tmu'] / 1e6

# Définir les périodes d’état
periodes = config['periodes']

def definir_periode(Tmu):
    for etat, ranges in periodes.items():
        for start, end in ranges:
            if start <= Tmu <= end:
                return etat.upper()
    return 'REJETE'

df['Etat'] = df['Tmu'].apply(definir_periode)

# Comptage des événements par état
comptage_eveil = df[df['Etat'] == 'EVEIL']['Electrode'].value_counts()
comptage_sommeil = df[df['Etat'] == 'SOMMEIL']['Electrode'].value_counts()

# --- CAMEMBERTS ---
def creer_et_sauvegarder_camembert(data, titre, nom_fichier):
    plt.figure(figsize=(8, 8))
    plt.pie(data, labels=data.index, autopct='%1.1f%%', startangle=140)
    plt.title(titre)
    plt.axis('equal')
    plt.savefig(os.path.join(save_folder, nom_fichier))
    plt.close()

creer_et_sauvegarder_camembert(comptage_eveil, 'Répartition des pointes par électrode durant l\'éveil', f'{yaml_filename_prefix}_repartition_eveil.png')
creer_et_sauvegarder_camembert(comptage_sommeil, 'Répartition des pointes par électrode durant le sommeil', f'{yaml_filename_prefix}_repartition_sommeil.png')

# --- BARRES : Comptage brut éveil/sommeil ---
comptage_total = pd.DataFrame({'EVEIL': comptage_eveil, 'SOMMEIL': comptage_sommeil}).fillna(0)
comptage_total.plot(kind='bar', figsize=(12, 8), color=['blue', 'orange'])
plt.xlabel('Électrode')
plt.ylabel('Comptage des événements')
plt.title('Comptage des événements par électrode et par état')
plt.legend(title='État')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(save_folder, f'{yaml_filename_prefix}_ratios_par_electrode_et_periode.png'))
plt.show()

# --- NORMALISATION ---
durees = config['durees']
duree_eveil = durees['eveil']
duree_sommeil = durees['sommeil']

comptage_eveil_normalise = comptage_eveil / duree_eveil
comptage_sommeil_normalise = comptage_sommeil / duree_sommeil

ratios_normalises = comptage_eveil_normalise / comptage_sommeil_normalise

# --- BARRES : Ratios normalisés ---
ratios_normalises.plot(kind='bar', title='Ratios normalisés des événements (éveil/sommeil) par électrode')
plt.ylabel('Ratio normalisé')
plt.xlabel('Électrode')
plt.tight_layout()
plt.savefig(os.path.join(save_folder, f'{yaml_filename_prefix}_ratios_normalises.png'))
plt.show()

# --- BARRES : Fréquence normalisée par électrode ---
df_comptage = pd.DataFrame({
    'Éveil': comptage_eveil_normalise,
    'Sommeil': comptage_sommeil_normalise
}).fillna(0)

df_comptage.plot(kind='bar', figsize=(12, 6), color=['blue', 'orange'])
plt.title('Fréquence normalisée des événements par électrode (Éveil vs Sommeil)')
plt.ylabel('Fréquence normalisée')
plt.xlabel('Électrode')
plt.xticks(rotation=45)
plt.legend(title='Période')
plt.tight_layout()
plt.savefig(os.path.join(save_folder, f'{yaml_filename_prefix}_frequence_normalisee_par_electrode.png'))
plt.show()
