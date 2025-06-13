import numpy as np
import pandas as pd
import mne
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

# Charger le fichier CSV contenant les temps et les électrodes
df_csv = pd.read_csv('C:/Users/boyer/github/ECOFEC/data/raw/csv_file/7dcf931_19ICA_FINAL.csv')
# Convertir les Tmu en secondes
df_csv['Tmu'] = df_csv['Tmu'] / 1e6

# Définir le chemin du fichier EDF
edf_path = 'C:/Users/boyer/github/ECOFEC/data/cleaned/7dcf931af56bfa58ad45079194a0235b_clean.edf'

# Charger les données EDF avec MNE
raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
fs = int(raw.info['sfreq'])  # fréquence d'échantillonnage récupérée automatiquement

# Dictionnaire des canaux EDF pour chaque électrode (indices MNE, 0-based)
# Ici tu dois adapter selon les noms dans raw.ch_names
Electrode_map = {
    'C4': 'C4',
    'F8': 'F8',
    'F8-T4': ['F8', 'T4'],
    'T4/F8': ['T4', 'F8'],
    'T4': 'T4', 
    'F7/F3': ['F7', 'F3']
}

def low_pass_filter_derivative(data, sfreq, cutoff=80, order=2):
    nyquist = 0.5 * sfreq
    norm_cutoff = cutoff / nyquist
    b, a = butter(order, norm_cutoff, btype='low', analog=False)
    return lfilter(b, a, data)

def compute_slopes(window, peak_index, fs):
    derivative = np.diff(window) / (1/fs)
    derivative_smoothed = low_pass_filter_derivative(derivative, fs)
    max_negative_slope_idx = np.argmin(derivative_smoothed[max(0, peak_index - 15):peak_index + 1]) + max(0, peak_index - 15)
    negative_slope = derivative_smoothed[max_negative_slope_idx]
    max_positive_slope_idx = np.argmax(derivative_smoothed[peak_index:min(len(derivative_smoothed), peak_index + 20)]) + peak_index
    positive_slope = derivative_smoothed[max_positive_slope_idx]
    return negative_slope, positive_slope, derivative_smoothed, max_negative_slope_idx, max_positive_slope_idx

results = []

# Parcourir chaque électrode et chaque temps
for electrode in df_csv['Electrode'].unique():
    df_electrode = df_csv[df_csv['Electrode'] == electrode]
    chans = Electrode_map[electrode]
    if not isinstance(chans, list):
        chans = [chans]

    for tmu in df_electrode['Tmu']:
        center_idx = int(tmu * fs)
        start_idx = center_idx - int(0.2 * fs)
        end_idx = center_idx + int(0.2 * fs)

        # Vérifier validité de la fenêtre
        if start_idx < 0 or end_idx > len(raw.times):
            continue

        for ch_name in chans:
            window = raw.get_data(picks=ch_name)[:, start_idx:end_idx].flatten()

            restricted_start_idx = int(center_idx - 0.025 * fs)
            restricted_end_idx = int(center_idx + 0.02 * fs)
            restricted_window = window[restricted_start_idx - start_idx : restricted_end_idx - start_idx]

            peak_value = np.max(np.abs(restricted_window))
            peak_index = np.argmax(np.abs(restricted_window)) + (restricted_start_idx - start_idx)

            crossing_left_candidates = np.where(np.diff(np.sign(np.diff(window[:peak_index]))))[0]
            crossing_left_candidates = [idx for idx in crossing_left_candidates if idx <= (peak_index - 7)]
            crossing_left = crossing_left_candidates[-1] if len(crossing_left_candidates) > 0 else 0

            crossing_right_candidates = np.where(np.diff(np.sign(np.diff(window[peak_index:]))))[0]
            crossing_right_candidates = [idx for idx in crossing_right_candidates if idx >= 5]
            crossing_right = crossing_right_candidates[0] + peak_index + 1 if len(crossing_right_candidates) > 0 else len(window) - 1

            amplitude = peak_value - window[crossing_left]

            half_amplitude = -amplitude / 2

            left_idx = np.where(window[:peak_index] >= half_amplitude)[0]
            right_idx = np.where(window[peak_index:] >= half_amplitude)[0]

            if len(left_idx) > 0 and len(right_idx) > 0:
                left_half_width_point = left_idx[-1]
                right_half_width_point = peak_index + right_idx[0]
                half_width = right_half_width_point - left_half_width_point
            else:
                half_width = np.nan

            negative_slope, positive_slope, derivative_smoothed, max_negative_slope_idx, max_positive_slope_idx = compute_slopes(window, peak_index, fs)

            results.append([tmu, electrode, ch_name, amplitude, half_width, crossing_left, crossing_right, negative_slope, positive_slope])

            # Plot optionnel (tu peux commenter pour gagner du temps)
            #plt.figure()
            #plt.subplot(2, 1, 1)
            #plt.plot(window, label='Signal')
            #plt.axhline(y=half_amplitude, color='orange', linestyle='--', label='Half Amplitude')
            #plt.axvline(x=peak_index, color='g', linestyle='--', label='Peak')
            #plt.axvline(x=crossing_left, color='purple', linestyle='--', label='Crossing Left')
            #plt.axvline(x=crossing_right, color='purple', linestyle='--', label='Crossing Right')
            #plt.scatter(left_half_width_point, half_amplitude, color='blue', label='Left Half Width Point')
            #plt.scatter(right_half_width_point, half_amplitude, color='red', label='Right Half Width Point')
            #plt.gca().invert_yaxis()
            #plt.title(f'Electrode: {electrode}, Channel: {ch_name}, Tmu: {tmu}')
            #plt.xlabel('Index')
            #plt.ylabel('Amplitude')
            #plt.legend()

            #plt.subplot(2, 1, 2)
            #plt.plot(np.arange(len(derivative_smoothed)), derivative_smoothed, label='Dérivée filtrée', color='red')
            #plt.gca().invert_yaxis()
            #plt.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)
            #plt.scatter(max_positive_slope_idx, derivative_smoothed[max_positive_slope_idx], color='blue', label='Max Positive Slope')
            #plt.scatter(max_negative_slope_idx, derivative_smoothed[max_negative_slope_idx], color='green', label='Max Negative Slope')
            #plt.title(f'Dérivée de l\'IED {electrode} {ch_name}')
            #plt.xlabel('Index')
            #plt.ylabel('Dérivée (µV/s)')
            #plt.legend(loc='upper left')
            #plt.show()

# Convertir en DataFrame et sauvegarder
df_results = pd.DataFrame(results, columns=['Tmu', 'Electrode', 'Channel', 'Amplitude', 'Half_Width', 'Crossing_Left', 'Crossing_Right', 'Negative_Slope', 'Positive_Slope'])
df_results.to_csv('C:/Users/boyer/github/ECOFEC/Results/ied_morphology_results.csv', index=False)

print(df_results.head())
