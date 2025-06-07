# evt_cleaning.py

# ───────────────────────────────────────────────
# 1. Chargement des librairies
# ───────────────────────────────────────────────
import pandas as pd
import yaml

# ───────────────────────────────────────────────
# 2. Chargement de la configuration YAML
# ───────────────────────────────────────────────
with open(r"C:\Users\boyer\github\ECOFEC\data\config\config_evt_cleaning.yaml", "r") as f:
    config = yaml.safe_load(f)

input_evt_file = config["paths"]["input_evt_file"]
output_csv_file = config["paths"]["output_csv_file"]
output_evt_file = config["paths"]["output_evt_file"]

rename_dict = config["rename_dict"]
electrodes_interet = config["electrodes_interet"]
filter_comnt = config["filter_comnt"]
valeurs_a_exclure = config["valeurs_a_exclure"]
seuil = config["seuil"]  # en microsecondes
conditions = config["conditions"]

# ───────────────────────────────────────────────
# 3. Lecture du fichier EVT
# ───────────────────────────────────────────────
df = pd.read_csv(input_evt_file, sep="\t")

# ───────────────────────────────────────────────
# 4. Nettoyage structurel et filtrage initial
# ───────────────────────────────────────────────
df.columns = df.columns.str.strip()
print("Colonnes après strip :", df.columns)

if filter_comnt["mode"] == "exclude":
    df = df[~((df["Code"] == 2) & (~df["Comnt"].isin(filter_comnt["values"])))]

# ───────────────────────────────────────────────
# 5. Mapping des codes vers les noms d’électrodes
# ───────────────────────────────────────────────
df["Electrode"] = df["Code"].map(rename_dict).fillna("0")
print(df.head(20))

# ───────────────────────────────────────────────
# 6. Filtrage par électrodes d’intérêt
# ───────────────────────────────────────────────
df = df[df["Electrode"].isin(electrodes_interet)]
print("Électrodes d’intérêt :", electrodes_interet)
print("Occurrences par électrode :\n", df["Electrode"].value_counts())

# ───────────────────────────────────────────────
# 7. Recherche des événements proches dans le temps
# ───────────────────────────────────────────────
def trouver_Electrodes_proches(df, seuil):
    resultats = []
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            diff_temps = abs(df.iloc[i]["Tmu"] - df.iloc[j]["Tmu"])
            if diff_temps <= seuil:
                resultats.append((
                    df.iloc[i]["Electrode"], df.iloc[i]["Tmu"],
                    df.iloc[j]["Electrode"], df.iloc[j]["Tmu"],
                    diff_temps
                ))
    return resultats

Electrodes_proches = trouver_Electrodes_proches(df, seuil)

if not Electrodes_proches:
    print("Aucun événement proche trouvé.")
    df.to_csv(output_csv_file, index=False)
else:
    print("Événements proches trouvés :")
    for e1, t1, e2, t2, diff in Electrodes_proches:
        print(f"{e1} ({t1}) et {e2} ({t2}) à {diff} µs d'écart.")

    # ───────────────────────────────────────────────
    # 9. Gestion des événements proches
    # ───────────────────────────────────────────────
    Electrodes_proches = pd.DataFrame(
        Electrodes_proches,
        columns=["Électrode 1", "Temps 1", "Électrode 2", "Temps 2", "Différence"]
    )
    Electrodes_proches["Combine"] = Electrodes_proches["Électrode 1"] + " et " + Electrodes_proches["Électrode 2"]
    print("Occurrences avant filtrage :\n", Electrodes_proches["Combine"].value_counts())

    Electrodes_temp = Electrodes_proches.copy()
    Electrodes_temp = Electrodes_temp[~Electrodes_temp["Combine"].isin(valeurs_a_exclure)]
    print("Valeurs exclues :", valeurs_a_exclure)
    print("Occurrences après filtrage :\n", Electrodes_temp["Combine"].value_counts())

    # ───────────────────────────────────────────────
    # 10. Création de la liste des événements à supprimer
    # ───────────────────────────────────────────────
    def ajouter_Electrode_temps(Electrode, temps):
        Electrodes_supprimees_list.append({"Electrode": Electrode, "Temps": temps})

    Electrodes_supprimees_list = []
    for i, row in Electrodes_temp.iterrows():
        for condition in conditions:
            if condition["combine"] in row["Combine"]:
                ajouter_Electrode_temps(condition["electrode"], row[condition["temps"]])

    Electrodes_supprimees_df = pd.DataFrame(Electrodes_supprimees_list)
    print("Événements à supprimer :\n", Electrodes_supprimees_df)

    # ───────────────────────────────────────────────
    # 11. Nettoyage des doublons
    # ───────────────────────────────────────────────
    print("Doublons Tmu :", Electrodes_supprimees_df["Temps"].duplicated().sum())
    print("Temps des doublons :", Electrodes_supprimees_df[Electrodes_supprimees_df.duplicated(subset=["Temps"], keep=False)]["Temps"])

    Electrodes_supprimees_df.drop_duplicates(subset=["Temps"], inplace=True)
    Electrodes_supprimees_df.rename(columns={"Temps": "Tmu"}, inplace=True)
    print("Après suppression des doublons :\n", Electrodes_supprimees_df["Electrode"].value_counts())

    # ───────────────────────────────────────────────
    # 12. Création du DataFrame final nettoyé
    # ───────────────────────────────────────────────
    df_final = df.copy()
    print("Avant suppression :", df_final["Electrode"].value_counts())

    df_final = df_final[~df_final["Tmu"].isin(Electrodes_supprimees_df["Tmu"])]
    print("Après suppression :", df_final["Electrode"].value_counts())

    df_final.to_csv(output_csv_file, index=False)

# ───────────────────────────────────────────────
# 13. Réécriture du fichier .evt final
# ───────────────────────────────────────────────
df_final = df_final.drop(columns=["Electrode"])
df_final.rename(columns={"Tmu": "Tmu    "}, inplace=True)
print("Colonnes finale :", df_final.columns)

# Padding des colonnes pour format .evt
df_final["Tmu    "] = df_final["Tmu    "].apply(lambda x: f"{x:<15}")
df_final["Code"] = df_final["Code"].astype(str).apply(lambda x: f"{x:<1}" if len(x) == 1 else f"{x:<2}")
df_final["TriNo"] = df_final["TriNo"].apply(lambda x: f"{x:<1}")
df_final["Comnt"] = df_final["Comnt"].apply(lambda x: f"{x:<40}")
df_final["Ver-C"] = df_final["Ver-C"].apply(lambda x: f"")

# En-tête formaté
header = "Tmu         	Code	TriNo	Comnt	Ver-C\n"

# Écriture du .evt
with open(output_evt_file, "w") as f:
    f.write(header)
    for _, row in df_final.iterrows():
        line = f"{row['Tmu    ']}\t{row['Code']}\t{row['TriNo']}\t{row['Comnt']}"
        f.write(line + "\n")
