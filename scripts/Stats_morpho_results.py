import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Charger les données
df_results = pd.read_csv(r'C:/Users/boyer/github/ECOFEC/Results/ied_morphology_results.csv')

# Définir les périodes
eveil_periods = [[0, 169], [278, 600], [2248, 2404]]
sommeil_periods = [[960, 2248]]

def get_etat(tmu):
    for start, end in eveil_periods:
        if start <= tmu <= end:
            return 'Eveil'
    for start, end in sommeil_periods:
        if start <= tmu <= end:
            return 'Sommeil'
    return 'Hors_Periode'

df_results['Periode'] = df_results['Tmu'].apply(get_etat)
df_results = df_results[df_results['Periode'] != 'Hors_Periode']

# Variables morphologiques à analyser
morpho_vars = ['Amplitude', 'Half_Width', 'Negative_Slope', 'Positive_Slope']

# Fonction pour détecter les outliers par électrode et période
def detect_outliers_iqr(sub_df, var):
    Q1 = sub_df[var].quantile(0.25)
    Q3 = sub_df[var].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return sub_df[(sub_df[var] < lower) | (sub_df[var] > upper)]

# Dictionnaire pour stocker les outliers
outliers_dict = {}

# Boucle pour chaque variable
for var in morpho_vars:
    outliers_list = []
    for (elec, per), group in df_results.groupby(['Electrode', 'Periode']):
        out = detect_outliers_iqr(group, var)
        out['Variable'] = var
        out['Electrode'] = elec
        out['Periode'] = per
        outliers_list.append(out)
    outliers_dict[var] = pd.concat(outliers_list) if outliers_list else pd.DataFrame()

# Fusionner tous les outliers
df_outliers = pd.concat(outliers_dict.values(), ignore_index=True)

# 🖼️ Violin + outliers en overlay
for var in morpho_vars:
    plt.figure(figsize=(14, 6))
    sns.violinplot(x='Electrode', y=var, hue='Periode', data=df_results, inner=None)
    sns.stripplot(x='Electrode', y=var, hue='Periode', data=outliers_dict[var], 
                  dodge=True, marker='x', color='red', alpha=0.7, jitter=0.2, linewidth=1.2)
    plt.title(f'{var} par électrode et période (Outliers en rouge)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend(title='Période')
    plt.show()
