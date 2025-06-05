import os
import pandas as pd
import yaml


def charger_config(chemin_config):
    with open(chemin_config, 'r') as f:
        return yaml.safe_load(f)


def nettoyer_colonnes(df):
    # Ne garder que les colonnes importantes et supprimer les lignes sans annotation
    colonnes_gardees = ['Time', 'Comnt', 'Dur']
    df = df.drop(columns=[col for col in df.columns if col not in colonnes_gardees], errors='ignore')
    df = df.dropna(subset=['Comnt'])
    return df


def filtrer_comnt(df, filter_comnt):
    mode = filter_comnt.get('mode', 'exclude').lower()
    valeurs = filter_comnt.get('values', [])
    if not valeurs:
        return df  # Rien à filtrer

    pattern = '|'.join(valeurs)
    if mode == 'exclude':
        masque = ~df['Comnt'].str.contains(pattern, na=False)
    elif mode == 'include':
        masque = df['Comnt'].str.contains(pattern, na=False)
    else:
        raise ValueError(f"Mode de filtrage inconnu : {mode}")

    return df[masque].reset_index(drop=True)


def trouver_evenements_proches(df, seuil):
    combinaisons_proches = []
    n = len(df)
    for i in range(n):
        t1 = df.loc[i, 'Time']
        for j in range(i + 1, n):
            t2 = df.loc[j, 'Time']
            diff = abs(t2 - t1)
            if diff <= seuil:
                combinaisons_proches.append((i, j))
            elif (t2 - t1) > seuil:
                break  # optimisation : les temps sont triés
    return combinaisons_proches


def appliquer_filtrage_doublons(df, combinaisons_proches):
    a_supprimer = set()
    for i, j in combinaisons_proches:
        annot_i = df.loc[i, 'Comnt']
        annot_j = df.loc[j, 'Comnt']

        # Logique de suppression selon la similarité des annotations
        if annot_i == annot_j:
            a_supprimer.add(j)
        elif annot_i in annot_j:
            a_supprimer.add(i)
        elif annot_j in annot_i:
            a_supprimer.add(j)
        elif annot_i > annot_j:
            a_supprimer.add(i)
        else:
            a_supprimer.add(j)

    df_filtre = df.drop(index=list(a_supprimer)).reset_index(drop=True)
    return df_filtre


def renommer_annotations(df, rename_dict):
    # Remplace les codes d’électrodes par des labels plus lisibles dans la colonne 'Comnt'
    def remplacer(texte):
        for code, label in rename_dict.items():
            # code est un int dans YAML, transformer en str pour chercher dans texte
            if str(code) in texte:
                texte = texte.replace(str(code), label)
        return texte

    df['Comnt'] = df['Comnt'].apply(remplacer)
    return df


def exporter_fichiers(df, output_csv, output_evt):
    # Export CSV classique
    df.to_csv(output_csv, index=False)

    # Export EVT (format tabulé sans en-tête)
    df_evt = pd.DataFrame({
        'Time': df['Time'],
        'Comnt': df['Comnt'],
        'Dur': df['Dur'],
        'Ver-C': [''] * len(df)
    })
    df_evt.to_csv(output_evt, sep='\t', index=False, header=False)


def nettoyer_evt():
    # Charger la config
    chemin_config = "data/config/config_evt_cleaning.yaml"
    config = charger_config(chemin_config)


    # Extraire paramètres
    input_file = config['paths']['evt_file']
    output_csv = config['paths']['output_csv_file']
    output_evt = config['paths']['output_evt_file']

    seuil = config['params']['seuil_proximite']
    valeurs_exclues = config['params']['valeurs_a_exclure']
    filter_comnt = config['params'].get('filter_comnt', {'mode': 'exclude', 'values': []})
    rename_dict = config['params'].get('rename_dict', {})

    # Charger le fichier EVT brut
    df = pd.read_csv(input_file, sep='\t', names=['Time', 'Comnt', 'Dur', 'Ver-C'], skiprows=1)

    # Nettoyage de base
    df = nettoyer_colonnes(df)

    # Filtrage selon la colonne 'Comnt' (exclude/include)
    df = filtrer_comnt(df, filter_comnt)

    # Renommer les annotations
    df = renommer_annotations(df, rename_dict)

    # Trier par temps
    df = df.sort_values('Time').reset_index(drop=True)

    # Trouver événements proches
    combinaisons = trouver_evenements_proches(df, seuil)

    # Filtrer doublons
    df = appliquer_filtrage_doublons(df, combinaisons)

    # Exporter résultats
    exporter_fichiers(df, output_csv, output_evt)

    print(f"Nettoyage terminé : fichiers exportés\n- CSV : {output_csv}\n- EVT : {output_evt}")


if __name__ == "__main__":
    nettoyer_evt()
