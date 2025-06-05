import os
import mne

def preprocess_eeg_edf(edf_path, channels_of_interest=None, l_freq=1.5, h_freq=80, notch_freq=50):
    """
    Preprocess an EEG EDF file:
    - Loads EDF file
    - Selects specified channels
    - Applies notch filter and bandpass filter
    - Returns filtered raw data
    """
    # Load raw EDF data
    raw = mne.io.read_raw_edf(edf_path, preload=True)

    # Définir les canaux d’intérêt
    channels_of_interest = [
        'Fp1', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8',
        'T3', 'C3', 'Cz', 'C4', 'T4',
        'T5', 'P3', 'Pz', 'P4', 'T6',
        'O1', 'O2'
    ]

    # Garde uniquement les canaux présents dans le fichier
    available_channels = [ch for ch in channels_of_interest if ch in raw.ch_names]
    raw.pick_channels(available_channels)

    # Select channels if specified
    if channels_of_interest is not None:
        raw.pick_channels(channels_of_interest)

    # Copy raw to avoid modifying original
    raw_filtered = raw.copy()

    # Apply notch filter (remove powerline noise)
    raw_filtered.notch_filter(freqs=notch_freq, fir_design='firwin')

    # Apply bandpass filter
    raw_filtered.filter(l_freq=l_freq, h_freq=h_freq, fir_design='firwin')

    return raw_filtered

def clean_edf(input_file, output_file, channels_of_interest=None, l_freq=1.5, h_freq=80, notch_freq=50, plot=False):
    """
    Complete preprocessing + saving of cleaned file.
    """
    # Prétraitement
    raw_clean = preprocess_eeg_edf(input_file, channels_of_interest, l_freq, h_freq, notch_freq)

    # Sauvegarde : ici au format .fif (format MNE), plus adapté que EDF pour les fichiers traités
    if not output_file.endswith('.fif'):
        output_file = os.path.splitext(output_file)[0] + '-cleaned.fif'
    raw_clean.save(output_file, overwrite=True)

    # Optionnel : afficher le signal nettoyé
    if plot:
        raw_clean.plot()

from mne.export import export_raw

def clean_and_save_edf(edf_path, output_path, channels_of_interest=None, l_freq=1.5, h_freq=80, notch_freq=50, plot=False):
    raw_clean = preprocess_eeg_edf(edf_path, channels_of_interest, l_freq, h_freq, notch_freq)
    raw_clean.export(output_path, fmt='edf')
