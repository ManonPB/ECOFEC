import mne
import numpy as np
import scipy.io as sio
import argparse
import matplotlib.pyplot as plt

print("Début script")

def is_in_wake_period(start_sec, end_sec, wake_periods):
    """
    Vérifie si un segment (start_sec, end_sec) est entièrement inclus dans une période d'éveil.
    """
    for wstart, wend in wake_periods:
        if start_sec >= wstart and end_sec <= wend:
            return True
    return False

def extract_clean_segments(edf_path, pointes_mat_path, output_path,
                           min_seg_sec=1, total_duration_sec=60,
                           wake_periods=None,
                           visualize_segments=False):
    # --- Charger les données EEG .edf ---
    raw = mne.io.read_raw_edf(edf_path, preload=True)
    sfreq = raw.info['sfreq']
    n_samples = raw.n_times
    duration_sec = n_samples / sfreq
    print(f"EDF loaded: {edf_path}, Fs = {sfreq} Hz, Duration = {duration_sec:.1f} s")

    # --- Charger les pointes depuis .mat ---
    mat = sio.loadmat(pointes_mat_path)
    onsets = mat['onsets'].squeeze()  # en secondes
    duration = 0.3  # durée moyenne d'une pointe en secondes (à adapter si besoin)

    # Création de pointes [début, fin]
    pointes = np.stack([onsets, onsets + duration], axis=1)
    print(f"{pointes.shape[0]} pointes reconstruites à partir des onsets.")

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

    # --- Filtrer les segments dans les périodes d'éveil ---
    if wake_periods is not None:
        wake_segments = []
        for seg_start, seg_end in clean_segments:
            start_sec = seg_start / sfreq
            end_sec = seg_end / sfreq
            if is_in_wake_period(start_sec, end_sec, wake_periods):
                wake_segments.append((seg_start, seg_end))
        print(f"{len(wake_segments)} segments propres dans les périodes d'éveil.")
    else:
        wake_segments = clean_segments

    # --- Sélection interactive avec visualisation ---
    selected_data = []
    total_samples = 0
    segment_count = 0

    for start, end in wake_segments:
        seg_len = end - start
        segment_count += 1

        if visualize_segments:
            data_plot = raw.get_data(start=start, stop=end)
            times = np.arange(data_plot.shape[1]) / sfreq
            plt.figure(figsize=(10, 4))
            plt.title(f'Segment {segment_count}: {start/sfreq:.1f}s - {end/sfreq:.1f}s')
            plt.plot(times, data_plot[0, :])  # Affiche le canal 0 (modifiable)
            plt.xlabel('Temps (s)')
            plt.ylabel('Amplitude (uV)')
            plt.show()

            # Interaction utilisateur pour garder/rejeter
            keep = input("Garder ce segment ? (o/n) : ").strip().lower()
            while keep not in ('o', 'n'):
                keep = input("Réponse invalide, taper 'o' pour garder ou 'n' pour rejeter : ").strip().lower()

            if keep == 'n':
                print(f"Segment {segment_count} rejeté.")
                continue  # passe au segment suivant

        # Ajouter segment gardé
        selected_data.append(raw.get_data(start=start, stop=end))
        total_samples += seg_len

        if total_samples >= total_duration_sec * sfreq:
            print(f"Durée totale atteinte avec {segment_count} segments.")
            break

    if total_samples < total_duration_sec * sfreq:
        print(f"⚠️ Moins de {total_duration_sec} secondes de données propres sélectionnées après rejet.")
    else:
        print(f"✅ {total_duration_sec} secondes de données propres sélectionnées.")

    # --- Concaténer et créer nouveau RawArray ---
    if len(selected_data) == 0:
        print("Aucun segment sélectionné, sortie annulée.")
        return

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
    parser.add_argument("pointes_mat_path", help="Fichier .mat contenant 'onsets' (en secondes)")
    parser.add_argument("--output_path", default="clean_resting.fif", help="Fichier de sortie (.fif ou .edf)")
    parser.add_argument("--min_seg_sec", type=int, default=2, help="Durée minimale des segments (s)")
    parser.add_argument("--total_duration_sec", type=int, default=60, help="Durée totale souhaitée (s)")
    parser.add_argument("--visualize", action='store_true', help="Afficher les segments sélectionnés")
    parser.add_argument("--wake_periods", type=str,
                        help="Périodes d'éveil (paires start end en secondes) séparées par espace, ex: --wake_periods \"15 600 2248 2407\"")

    args = parser.parse_args()

    # Construire la liste des périodes d'éveil depuis la CLI
    if args.wake_periods:
        wake_vals = list(map(float, args.wake_periods.strip().split()))
        if len(wake_vals) % 2 == 0:
            wake_periods = [(wake_vals[i], wake_vals[i+1]) for i in range(0, len(wake_vals), 2)]
        else:
            print("⚠️ Nombre impair de valeurs pour --wake_periods, ignoré")
            wake_periods = None
    else:
        wake_periods = None

    extract_clean_segments(args.edf_path, args.pointes_mat_path, args.output_path,
                           min_seg_sec=args.min_seg_sec,
                           total_duration_sec=args.total_duration_sec,
                           wake_periods=wake_periods,
                           visualize_segments=args.visualize)
