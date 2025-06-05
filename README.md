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

You may use a virtual environment to avoid dependency conflicts:

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Preprocessing EEG EDF files
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
│
├── data/
│   ├── raw/            # Raw EEG EDF files (local only, gitignored)
│   └── cleaned/        # Preprocessed EEG files (local only, gitignored)
│
├── preprocessing/
│   └── edf_cleaning.py # Core EEG preprocessing functions
│
├── scripts/
│   └── preprocess_edf.py # CLI script to run preprocessing
│
├── .gitignore
├── requirements.txt
└── README.md

Created by Manon Boyer - ECOFEC Project
