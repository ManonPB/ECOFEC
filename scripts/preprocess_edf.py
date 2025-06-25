"""
Script de prétraitement des fichiers EEG au format EDF.

Ce script permet de nettoyer et filtrer des fichiers EDF (électroencéphalogrammes) en appliquant :
- une sélection optionnelle des canaux d'intérêt,
- un filtrage passe-bande (avec coupures basses et hautes fréquences paramétrables),
- un filtre en peigne (notch) pour supprimer le bruit à une fréquence spécifique (par défaut 50 Hz).

Il peut traiter un fichier EDF unique ou un dossier contenant plusieurs fichiers EDF, 
et sauvegarde les fichiers nettoyés dans un dossier de sortie spécifié.

Options disponibles :
- Choix des canaux à conserver
- Fréquences de filtrage ajustables
- Possibilité de forcer l'écrasement des fichiers déjà traités
- Option pour afficher un tracé des signaux nettoyés

Usage typique en ligne de commande :
(venv) PS C:\Users\boyer\github\ECOFEC> python -m scripts.preprocess_edf data/raw/edf_file --output_dir data/cleaned --plot  

"""

import os
import argparse
from preprocessing.edf_cleaning import clean_and_save_edf

def parse_args():
    parser = argparse.ArgumentParser(description="Preprocess EDF EEG files")
    parser.add_argument("input_path", type=str, help="Path to .edf file or folder containing EDF files")
    parser.add_argument("--output_dir", type=str, default="data/cleaned", help="Directory to save cleaned EDF files")
    parser.add_argument("--channels", nargs="+", default=None, help="List of channels to keep")
    parser.add_argument("--l_freq", type=float, default=1.5, help="Low frequency cutoff for filtering")
    parser.add_argument("--h_freq", type=float, default=80.0, help="High frequency cutoff for filtering")
    parser.add_argument("--notch_freq", type=float, default=50.0, help="Notch filter frequency")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing cleaned files")
    parser.add_argument("--plot", action="store_true", help="Plot cleaned signals after preprocessing")
    return parser.parse_args()

def main():
    args = parse_args()

    input_files = []
    if os.path.isdir(args.input_path):
        input_files = [os.path.join(args.input_path, f)
                       for f in os.listdir(args.input_path) if f.endswith(".edf")]
    elif args.input_path.endswith(".edf"):
        input_files = [args.input_path]
    else:
        raise ValueError("Input must be a .edf file or a directory containing .edf files.")

    os.makedirs(args.output_dir, exist_ok=True)

    for edf_path in input_files:
        file_name = os.path.splitext(os.path.basename(edf_path))[0]
        output_path = os.path.join(args.output_dir, f"{file_name}_clean.edf")

        if os.path.exists(output_path) and not args.overwrite:
            print(f"File already exists: {output_path}. Use --overwrite to force overwrite.")
            continue

        print(f"Processing: {edf_path}")
        try:
            clean_and_save_edf(
                edf_path,
                output_path,
                channels_of_interest=args.channels,
                l_freq=args.l_freq,
                h_freq=args.h_freq,
                notch_freq=args.notch_freq
            )
            print(f"Saved cleaned file to: {output_path}\n")
        except Exception as e:
            print(f"Error processing {edf_path}: {e}")

if __name__ == "__main__":
    main()
