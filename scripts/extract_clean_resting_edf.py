import mne
import numpy as np
import scipy.io as sio
import argparse

print("Début script")

def extract_clean_segments(edf_path, pointes_mat_path, output_path,
                           min_seg_sec=1, total_duration_sec=60):
    # --- Charger les données EEG .edf ---
    raw = mne.io.read_raw_edf(edf_path, preload=True)
    sfreq = raw.info['sfreq']
    n_samples = raw.n_times
    duration_sec = n_samples / sfreq
    print(f"EDF loaded: {edf_path}, Fs = {sfreq} Hz, Duration = {duration_sec:.1f} s")

    # --- Charger les pointes depuis .mat ---
    mat = sio.loadmat(pointes_mat_path)

    # On utilise la variable 'onsets' (1xN)
    onsets = mat['onsets'].squeeze()  # en secondes
    duration = 0.3  # durée moyenne d'une pointe en secondes (à adapter si besoin)

    # Création de pointes [début, fin]
    pointes = np.stack([onsets, onsets + duration], axis=1)
    print(f"{pointes.shape[0]} pointes reconstruites à partir des onsets.")


    print(f"{pointes.shape[0]} pointes chargées.")

    # --- Vecteur binaire d'artéfacts ---
    artifact_vector = np.zeros(n_samples, dtype=int)
    for start_sec, end_sec in pointes:
        start_idx = max(0, int(round(start_sec * sfreq)))
        end_idx = min(n_samples, int(round(end_sec * sfreq)))
        artifact_vector[start_idx:end_idx] = 1

    # --- Détection des segments clean ---
    min_samples = int(min_seg_sec * sfreq)
    clean_segments = []
    current_start = None
    for i in range(n_samples):
        if artifact_vector[i] == 0 and current_start is None:
            current_start = i
        elif artifact_vector[i] == 1 and current_start is not None:
            if i - current_start >= min_samples:
                clean_segments.append((current_start, i))
            current_start = None
    if current_start is not None and (n_samples - current_start) >= min_samples:
        clean_segments.append((current_start, n_samples))

    print(f"{len(clean_segments)} segments propres trouvés (≥ {min_seg_sec}s).")

    # --- Sélectionner segments jusqu'à 1 min cumulées ---
    selected_data = []
    total_samples = 0
    for start, end in clean_segments:
        seg_len = end - start
        selected_data.append(raw.get_data(start=start, stop=end))
        total_samples += seg_len
        if total_samples >= total_duration_sec * sfreq:
            break

    if total_samples < total_duration_sec * sfreq:
        print("⚠️ Moins de 1 minute de données propres disponibles.")
    else:
        print("✅ 1 minute de données propres sélectionnées.")

    # --- Concaténer et créer nouveau RawArray ---
    concat_data = np.concatenate(selected_data, axis=1)
    info = raw.info.copy()
    clean_raw = mne.io.RawArray(concat_data, info)

    # --- Sauvegarde ---
    if output_path.endswith('.edf'):
        clean_raw.export(output_path, fmt='edf', overwrite=True)
    else:
        clean_raw.save(output_path, overwrite=True)

    print(f"✅ Données sauvegardées : {output_path}")


# --- Exécution en ligne de commande ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extraction de segments EEG propres (sans pointes)")
    parser.add_argument("edf_path", help="Chemin vers le fichier .edf")
    parser.add_argument("pointes_mat_path", help="Fichier .mat contenant 'pointes' (Nx2, en secondes)")
    parser.add_argument("--output_path", default="clean_resting.fif", help="Fichier de sortie (.fif ou .edf)")
    parser.add_argument("--min_seg_sec", type=int, default=2, help="Durée minimale des segments (s)")
    parser.add_argument("--total_duration_sec", type=int, default=180, help="Durée totale souhaitée (s)")

    args = parser.parse_args()

    extract_clean_segments(args.edf_path, args.pointes_mat_path, args.output_path,
                           min_seg_sec=args.min_seg_sec,
                           total_duration_sec=args.total_duration_sec)
