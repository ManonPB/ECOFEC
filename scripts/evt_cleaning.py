import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt 
import seaborn as sns
import yaml

# Charger le fichier de configuration YAML
with open('C:/Users/boyer/github/ECOFEC/data/config/config_evt_cleaning.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Lire les chemins d'accès et autres variables depuis la configuration
input_file = config['input_evt_file']
output_csv_file = config['output_csv_file']
output_evt_file = config['output_evt_file']
rename_dict = config['rename_dict']
electrodes_interet = config['electrodes_interet']
seuil = config['seuil']
valeurs_a_exclure = config['valeurs_a_exclure']
filter_comnt = config['filter_comnt']

# Lire le fichier .evt
df = pd.read_csv(input_file, delimiter='\t')  

df.head(20)

print(df.columns)

# Il y a des espaces après Tmu, on les supprime juste pour faire tourner le script et éviter les bugs.
# Pour supprimer des espaces ou des caractères inattendus :
df.columns = df.columns.str.strip()

# Afficher les noms des colonnes
print(df.columns)

# Supprimer les lignes comprenant les annotations des cliniciens, en conservant les éventuels marquages de pointes                                     '
if filter_comnt['mode'] == 'exclude': 
    df = df[~((df['Code'] == 2) & (~df['Comnt'].isin(filter_comnt['values'])))]

#Si on veut vérifier ce qu'il conserve
print(filter_comnt['values'])

# Créer une nouvelle colonne 'Electrode' en utilisant le dictionnaire de mappage
df['Electrode'] = df['Code'].map(rename_dict).fillna('0')

# Afficher les premières lignes du DataFrame pour vérifier
df.head(20)

# Filtrer le DataFrame pour inclure seulement les électrodes d'intérêt 
df = df[df['Electrode'].isin(electrodes_interet)]
print(electrodes_interet)

# Compter le nombre d'occurrences de chaque Electrode 
compte_Electrodes = df['Electrode'].value_counts() 
# Afficher les résultats 
print(compte_Electrodes)

# Trouver les pointes à moins de 25 millisecondes de différence
# Pour rappel, ici Tmu est en microsecondes
# 0,025 secondes font 25 millisecondes ou 25 000 microsecondes
def trouver_Electrodes_proches(df, seuil):
    resultats = []
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            diff_temps = abs(df.iloc[i]['Tmu'] - df.iloc[j]['Tmu'])
            if diff_temps <= seuil:
                resultats.append((df.iloc[i]['Electrode'], df.iloc[i]['Tmu'], 
                                  df.iloc[j]['Electrode'], df.iloc[j]['Tmu'], 
                                  diff_temps))
    return resultats

# Obtenir les résultats
Electrodes_proches = trouver_Electrodes_proches(df, seuil)

# Affichage des résultats
for e1, t1, e2, t2, diff in Electrodes_proches:
    print(f"Electrodes {e1} ({t1} microsecondes) et {e2} ({t2} microsecondes) sont à {diff} microsecondes d'écart.")

# Créer un DataFrame avec les résultats
Electrodes_proches = pd.DataFrame(trouver_Electrodes_proches(df, seuil), columns=['Électrode 1', 'Temps 1 (s)', 'Électrode 2', 'Temps 2 (s)', 'Différence (s)'])

# Ajouter une colonne 'Combine' avec 'et' comme séparateur
Electrodes_proches['Combine'] = Electrodes_proches['Électrode 1'] + " et " + Electrodes_proches['Électrode 2']

# Compter le nombre d'occurrences de chaque électrode 
compte_occurence = Electrodes_proches['Combine'].value_counts() 
# Afficher les résultats 
print(compte_occurence)

# Copier le DataFrame des Electrodes proches pour travailler dessus
Electrodes_temp = Electrodes_proches.copy()

# Si jamais il y a des valeurs que nous souhaitons conservées même si elles sont proches
Electrodes_temp = Electrodes_temp[~Electrodes_temp['Combine'].isin(valeurs_a_exclure)]
print(valeurs_a_exclure)

# Compter de nouveau le nombre d'occurrences de chaque combinaison après filtrage
compte_occurence_apres_filtrage = Electrodes_temp['Combine'].value_counts()

# Afficher les résultats après filtrage
print("\nNombre d'occurrences pour chaque combinaison après filtrage :")
print(compte_occurence_apres_filtrage)

# Fonction pour ajouter l'électrode et le temps
def ajouter_Electrode_temps(Electrode, temps):
    Electrodes_supprimees_list.append({'Electrode': Electrode, 'Temps': temps})

# Liste pour stocker les résultats
Electrodes_supprimees_list = []

# Boucle à travers le DataFrame
for i, row in Electrodes_temp.iterrows(): 
    combine = row['Combine'] 
    # Afficher les conditions pour vérification 
    print(f"Vérification des conditions pour 'Combine': {combine}")
    for condition in config['conditions']: 
        if condition['combine'] in combine: 
            ajouter_Electrode_temps(condition['electrode'], row[condition['temps']])

# Convertir la liste en DataFrame
Electrodes_supprimees_df = pd.DataFrame(Electrodes_supprimees_list)

# Afficher le résultat
print(Electrodes_supprimees_df)

# Compter le nombre d'occurrences de chaque électrode
test = Electrodes_supprimees_df['Electrode'].value_counts()

# Afficher les résultats
print("\nLes events par electrode qui seront par la suite supprimées dans le fichier final sont :")
print(test)

#On renomme 'Temps' en 'Tmu'
Electrodes_supprimees_df.rename(columns={'Temps': 'Tmu'}, inplace=True)

# Vérifier les doublons dans Electrodes_supprimees_df
doublons = Electrodes_supprimees_df['Tmu'].duplicated().sum()
print(f"Nombre de doublons dans Electrodes_supprimees_df['Tmu'] : {doublons}")

# Trouver les valeurs de Tmu en double
doublons_tmps = Electrodes_supprimees_df[Electrodes_supprimees_df.duplicated(subset=['Tmu'], keep=False)]

# Afficher les temps des doublons
print("\nTemps des doublons dans Electrodes_supprimees_df['Tmu'] :")
print(doublons_tmps['Tmu'])

# Supprimer les doublons basés sur 'Tmu'
Electrodes_supprimees_df = Electrodes_supprimees_df.drop_duplicates(subset=['Tmu'])

# Recompter le nombre d'occurrences de chaque électrode après suppression des doublons
test = Electrodes_supprimees_df['Electrode'].value_counts()
print("\nCompter le nombre d'occurrences de chaque électrode après suppression des doublons :")
print(test)

# Créer une copie du df initial
df_final = df.copy()
df_final.info()

# Compter le nombre d'occurrences de chaque électrode 
initial = df_final['Electrode'].value_counts() 
# Afficher les résultats 
print(initial)

#on supprime de df_final les valeurs contenues dans Electrodes_supprimees_df
df_final = df_final[~df_final['Tmu'].isin(Electrodes_supprimees_df['Tmu'])]

# Compter le nombre d'occurrences de chaque électrode pour vérifier si la suppression a bien fonctionnée
verif2 = df_final['Electrode'].value_counts() 
# Afficher les résultats 
print(verif2)

df_final.to_csv(output_csv_file, index=False)

df_final = df_final.drop(columns=['Electrode'])
df_final = df_final.rename(columns={'Tmu': 'Tmu    '})

#print(df_final.columns)
print(df_final.columns)

# Formater les colonnes des données avec des tabulations pour un alignement spécifique
df_final['Tmu    '] = df_final['Tmu    '].apply(lambda x: f"{x:<15}")
df_final['Code'] = df_final['Code'].astype(str).apply(lambda x: f"{x:<1}" if len(x) == 1 else f"{x:<2}")
df_final['TriNo'] = df_final['TriNo'].apply(lambda x: f"{x:<1}")
df_final['Comnt'] = df_final['Comnt'].apply(lambda x: f"{x:<40}")  # 40 caractères pour Comnt
df_final['Ver-C'] = df_final['Ver-C'].apply(lambda x: f"")

# Spécifier les espaces de remplissage pour les en-têtes avec des séparateurs
header = "Tmu         	Code	TriNo	Comnt	Ver-C\n"

# Enregistrer le DataFrame dans un fichier .evt en utilisant des tabulations sans retour chariot supplémentaire sauf la première ligne
with open(output_evt_file, 'w') as f:
    f.write(header)
    for index, row in df_final.iterrows():
        line = f"{row['Tmu    ']}\t{row['Code']}\t{row['TriNo']}\t{row['Comnt']}"
        f.write(line + '\n')

df.to_csv(output_csv_file, index=False)