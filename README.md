# ECOFEC
Multimodal EEG analysis scripts for the ECOFEC project, which investigates the impact of interictal epileptiform discharges (IEDs) on cognitive development in children with epilepsy.

# ECOFEC - EEG Data Preprocessing and Analysis

This repository contains scripts and tools for preprocessing and analyzing EEG data related to the ECOFEC project (Influence of Interictal Epileptic Discharges on Cognitive Development in Pediatric Epilepsy).

---

## Table of Contents

- [Project Description](#project-description)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Data Privacy and Security](#data-privacy-and-security)  
- [Repository Structure](#repository-structure)  

---

## Project Description

The ECOFEC project focuses on understanding how interictal epileptic discharges (IEDs) impact brain connectivity and cognitive development in children with epilepsy. This repository provides preprocessing pipelines for EDF EEG files, including filtering, channel selection, and artifact removal, to facilitate downstream analyses.

---

## Installation

This project requires Python 3.8+ and several scientific libraries. You can install the dependencies with:

```bash
pip install -r requirements.txt
```

Dependencies include:

mne

numpy

argparse

pandas

matplotlib

You may use a virtual environment to avoid dependency conflicts:

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Preprocessing EEG EDF files
The preprocessing script supports processing single EDF files or batches in a directory.

Basic example: process all EDF files in data/raw/ and save cleaned files in data/cleaned/:
```bash
python scripts/preprocess_edf.py data/raw/ --plot
```

Process a single file with overwrite:
```bash
python scripts/preprocess_edf.py data/raw/sample.edf --overwrite
```

Arguments

input_path: Path to EDF file or directory of EDF files

--output_dir: Directory where cleaned files will be saved (default: data/cleaned)

--channels: List of channels to keep (default: standard 19 EEG channels)

--l_freq: Low cutoff frequency for bandpass filter (default: 1.5 Hz)

--h_freq: High cutoff frequency for bandpass filter (default: 80 Hz)

--notch_freq: Frequency for notch filter (default: 50 Hz)

--plot: Plot cleaned signals after preprocessing (optional)

--overwrite: Overwrite existing cleaned files (optional)

2. Select events based on IED ratios
Once preprocessing is done, you can use select_IEDs.py to select IED events for further analysis based on event metadata and target ratio constraints.

Example usage:
```bash
python scripts/select_IEDs.py --periode matin --n_total 150
```

Arguments:

--periode: Period to analyze (e.g., matin, nuit, etc.)

--n_total: Total number of IEDs to select across all electrodes

Optional config and metadata paths can be provided if needed.

This ensures balanced selection across electrodes based on pre-defined IED distributions.

## Data Privacy and Security

This project processes sensitive EEG data related to pediatric epilepsy.
Important: Raw and cleaned EEG data files (*.edf) are NOT stored in this Git repository to protect patient confidentiality.

EEG data files must be stored locally on your computer, e.g., in data/raw/.

Processed files will be saved locally in data/cleaned/.

These folders are excluded from version control by .gitignore to avoid accidental upload.

Always provide local paths to data files when running scripts.

Do NOT commit or push any EEG data files or patient-identifiable information to GitHub or any public repository.

Following these guidelines helps ensure compliance with data protection regulations and maintain data privacy.

## Repository structure 

ECOFEC/
├── data/                          # Répertoire de données (non versionné)
│   ├── raw/                      # Données brutes (EDF, CSV, etc.)
│   │   ├── edf_file/            # Fichiers EEG bruts
│   │   ├── csv_file/            # Métadonnées ou annotations liées aux IEDs
│   ├── cleaned/                 # Données EEG nettoyées (après preprocessing)
│   ├── config/                  # Fichiers de configuration, dictionnaires, etc.
│
├── preprocessing/               # Fonctions de traitement EEG (modules Python)
│   ├── __init__.py
│   ├── edf_cleaning.py         # Fonctions de nettoyage EEG (filtres, sélection canaux, etc.)
│
├── scripts/                     # Scripts exécutables principaux
│   ├── preprocess_edf.py       # Script de prétraitement EDF
│   ├── select_IEDs.py          # Script de sélection d'évènements (IEDs) par période et par électrode
│
├── .gitignore                   # Fichiers/dossiers exclus du suivi Git
├── requirements.txt             # Dépendances Python nécessaires
├── README.md                    # Documentation principale du projet


Created by Manon Boyer - ECOFEC Project
