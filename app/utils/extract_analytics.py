import os
import librosa
import numpy as np
from scipy.stats import skew, kurtosis
from scipy.interpolate import interp1d


def round_floats(obj, precision=3):
    """Recursively rounds float values in a nested dictionary or list."""
    if isinstance(obj, dict):
        return {k: round_floats(v, precision) for k, v in obj.items()}
    if isinstance(obj, list):
        return [round_floats(i, precision) for i in obj]
    if isinstance(obj, float):
        return round(obj, precision)
    return obj

def to_native(obj):
    """Helper to convert numpy types to native python types for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.int_)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float_)):
        if np.isnan(obj):
            return None
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj

def get_feature_stats(feature_vector, feature_name):
    """Helper to calculate and return a dictionary of common statistics for a feature vector."""
    feature_vector = feature_vector.flatten()
    return {
        f"{feature_name}_mean": to_native(np.mean(feature_vector)),
        f"{feature_name}_std_dev": to_native(np.std(feature_vector)),
        f"{feature_name}_skewness": to_native(skew(feature_vector)),
        f"{feature_name}_kurtosis": to_native(kurtosis(feature_vector)),
        f"{feature_name}_median": to_native(np.median(feature_vector)),
        f"{feature_name}_min": to_native(np.min(feature_vector)),
        f"{feature_name}_max": to_native(np.max(feature_vector))
    }

def extract_music_analytics(audio_path: str, is_vocal_track: bool = False) -> dict:

    print(f"📈 Performing deep music analysis using librosa on: {audio_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at: {audio_path}")

    try:
        # --- 1. Load Audio & Basic Properties ---
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)
        y_harmonic, y_percussive = librosa.effects.hpss(y)

        # --- 2. Core Feature Extraction ---
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='frames')
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        onsets = librosa.onset.onset_detect(y=y_percussive, sr=sr, units='time')
        
        # --- 3. Comprehensive Feature Calculation ---
        # Tonal Features
        chroma = librosa.feature.chroma_stft(y=y_harmonic, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key_index = np.argmax(chroma_mean)
        estimated_key = keys[key_index]
        
        # --- FIX START ---
        # Determine mode (Major/Minor) using a music theory heuristic based on the chroma vector.
        # This replaces the incorrect call to a non-existent librosa function.
        major_third_index = (key_index + 4) % 12
        minor_third_index = (key_index + 3) % 12
        mode = "Major" if chroma_mean[major_third_index] > chroma_mean[minor_third_index] else "Minor"
        # --- FIX END ---
        
        # Spectral Features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spec_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        spec_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        spec_flatness = librosa.feature.spectral_flatness(y=y)[0]
        spec_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        tonnetz = librosa.feature.tonnetz(y=y_harmonic, sr=sr)

        # Dynamic Features
        rms = librosa.feature.rms(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]

        # Structural Analysis
        rec_matrix = librosa.segment.recurrence_matrix(librosa.feature.chroma_cens(y=y, sr=sr), mode='affinity')
        num_segments = max(2, min(int(duration / 20), 8)) # Heuristic for 2-8 segments
        boundaries_idx = librosa.segment.agglomerative(rec_matrix, k=num_segments)
        boundary_times = librosa.times_like(rec_matrix, axis=1)[boundaries_idx]
        segment_times = np.concatenate(([0], boundary_times, [duration]))
        song_segments = [
            {"segment_id": i + 1, "start_time": to_native(segment_times[i]), "end_time": to_native(segment_times[i+1])}
            for i in range(len(segment_times) - 1)
        ]

        # --- 4. Vocal Analysis (if applicable) ---
        vocal_analysis_results = {}
        if is_vocal_track:
            f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            f0_voiced = f0[voiced_flag & (f0 > 0)]
            if f0_voiced.size > 0:
                median_f0 = np.nanmedian(f0_voiced)
                vocal_analysis_results = {
                    "vocal_presence_score": to_native(np.mean(voiced_probs)),
                    "estimated_gender_by_f0": "Female" if median_f0 > 165 else "Male", # Simple heuristic
                    "pitch_analysis_hz": get_feature_stats(f0_voiced, "f0"),
                    "vibrato_likelihood": to_native(np.nanstd(f0_voiced))
                }
            else:
                vocal_analysis_results = {"vocal_presence_score": 0.0, "error": "No voiced frames detected."}

        # --- 5. Assemble Final JSON Output ---
        final_analytics = {
            "metadata": {
                "file_path": audio_path,
                "duration_seconds": to_native(duration),
                "sample_rate": sr,
            },
            "summary": {
                "tempo_bpm": to_native(tempo),
                "estimated_key": estimated_key,
                "key_confidence": to_native(np.max(chroma_mean) / (np.sum(chroma_mean) + 1e-7)),
                "mode": mode, # Use the correctly calculated mode
                "harmonic_to_percussive_ratio": to_native(np.mean(librosa.feature.rms(y=y_harmonic)[0]) / (np.mean(librosa.feature.rms(y=y_percussive)[0]) + 1e-7))
            },
            "rhythm_and_tempo": {
                "beat_count": len(beat_frames),
                "onset_count": len(onsets),
                "beat_times_sec": to_native(beat_times),
                "onset_times_sec": to_native(onsets),
                "onset_density_per_sec": to_native(len(onsets) / duration if duration > 0 else 0),
            },
            "timbre_and_spectral_properties": {
                "spectral_centroid": get_feature_stats(spec_centroid, "spectral_centroid"),
                "spectral_bandwidth": get_feature_stats(spec_bandwidth, "spectral_bandwidth"),
                "spectral_contrast": {
                    "contrast_bands_mean": to_native(np.mean(spec_contrast, axis=1)),
                    "contrast_bands_std_dev": to_native(np.std(spec_contrast, axis=1)),
                },
                "spectral_rolloff": get_feature_stats(spec_rolloff, "spectral_rolloff"),
                "spectral_flatness": get_feature_stats(spec_flatness, "spectral_flatness"),
                "mfccs": {
                    "num_mfccs": 20,
                    "mfccs_mean": to_native(np.mean(mfccs, axis=1)),
                    "mfccs_std_dev": to_native(np.std(mfccs, axis=1))
                }
            },
            "tonality_and_harmony": {
                "chroma_profile": to_native(chroma_mean),
                "tonnetz_features": {
                    "tonnetz_mean": to_native(np.mean(tonnetz, axis=1)),
                    "tonnetz_std_dev": to_native(np.std(tonnetz, axis=1)),
                }
            },
            "dynamics_and_loudness": {
                "rms_energy": get_feature_stats(rms, "rms_energy"),
                "zero_crossing_rate": get_feature_stats(zcr, "zcr"),
                "crest_factor": to_native(np.max(np.abs(y)) / (np.mean(rms) + 1e-7)),
            },
            "structural_analysis": {
                 "estimated_segment_count": len(song_segments),
                 "segments": song_segments
            }
        }
        
        if vocal_analysis_results:
            final_analytics["vocal_analysis"] = vocal_analysis_results

        print("✅ Deep music analysis complete.")
        return final_analytics

    except Exception as e:
        print(f"❌ An error occurred during deep audio analysis: {e}")
        return {"error": str(e), "file_path": audio_path}


# --- Helper to ensure JSON-safe outputs ---
def to_py_native(val):
    """
    Recursively converts numpy types within dictionaries and lists 
    to native Python types for JSON serialization.
    """
    if isinstance(val, dict):
        return {k: to_py_native(v) for k, v in val.items()}
    if isinstance(val, (np.ndarray, list)):
        return [to_py_native(v) for v in val]
    if isinstance(val, (np.int_, np.intc, np.intp, np.int8,
                        np.int16, np.int32, np.int64, np.uint8,
                        np.uint16, np.uint32, np.uint64)):
        return int(val)
    if isinstance(val, (np.float_, np.float16, np.float32, np.float64)):
        return float(val)
    if isinstance(val, (np.bool_)):
        return bool(val)
    return val

# --- Helper to create shorter arrays for visualization ---
def downsample_array(arr: np.ndarray, target_points: int = 150) -> np.ndarray:
    """
    Downsamples a numpy array to a target number of points using averaging.
    This is useful for storing a visual summary of data without the full resolution.
    """
    if arr is None or len(arr) <= target_points:
        return arr
    
    original_len = len(arr)
    chunk_size = max(1, original_len // target_points)
    trimmed_len = (original_len // chunk_size) * chunk_size
    arr_trimmed = arr[:trimmed_len]
    
    # Replace NaN (Not a Number) with a value that can be handled by the frontend
    arr_trimmed = np.nan_to_num(arr_trimmed, nan=0.0) 
    
    return arr_trimmed.reshape(-1, chunk_size).mean(axis=1)



def extract_vocal_analytics(audio_path: str) -> dict:
    """
    Extracts deep vocal analytics including pitch, loudness, timbre,
    a gender prediction, and a downsampled pitch graph.
    """
    try:
        # 1. Load Audio
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)

        if duration < 1.0: # Increased min duration for more stable analysis
            return {"error": "Audio duration is too short for meaningful analysis."}

        # 2. Core Pitch Analysis (using pYIN)
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7')
        )
        times = librosa.times_like(f0, sr=sr)
        voiced_f0 = f0[voiced_flag]
        f0[~voiced_flag] = np.nan

        if len(voiced_f0) < 10:
            return {"error": "No significant voiced sections found to analyze."}

        # 3. Loudness Analysis
        rms = librosa.feature.rms(y=y)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        avg_loudness_db = np.mean(rms_db)
        loudness_variation_db = np.std(rms_db)

        # 4. Vocal Quality Metrics
        f0_diff = np.abs(np.diff(voiced_f0))
        jitter_local = np.mean(f0_diff) / np.mean(voiced_f0) * 100

        rms_interpolator = interp1d(librosa.times_like(rms, sr=sr), rms, kind='linear', bounds_error=False, fill_value=0)
        rms_at_f0_times = rms_interpolator(times)
        voiced_rms = rms_at_f0_times[voiced_flag & (rms_at_f0_times > 0)]
        shimmer_local = 0
        if len(voiced_rms) > 1:
            amp_diff = np.abs(np.diff(voiced_rms))
            shimmer_local = np.mean(amp_diff) / np.mean(voiced_rms) * 100

        y_harmonic, _ = librosa.effects.hpss(y)
        noise_energy = np.sum(y**2) - np.sum(y_harmonic**2)
        hnr = 10 * np.log10(np.sum(y_harmonic**2) / noise_energy) if noise_energy > 0 else 50.0

        # 5. Timbral and Other Features
        avg_spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        avg_spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        avg_zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))

        # 6. Speech Rate (approximated by onsets)
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        speech_rate_onsets_sec = len(onsets) / duration if duration > 0 else 0

        # 7. Aggregate Results & Improved Gender Prediction
        avg_pitch_hz = np.nanmean(voiced_f0)
        median_pitch_hz = np.nanmedian(voiced_f0)
        p25_pitch_hz = np.nanpercentile(voiced_f0, 25) # The pitch below which 25% of notes fall
        min_pitch_hz = np.nanmin(voiced_f0)
        max_pitch_hz = np.nanmax(voiced_f0)

        # --- NEW: Multi-layered Gender Estimation Logic ---
        if p25_pitch_hz < 145:
            gender_prediction = "Male"
        elif avg_pitch_hz > 185 and p25_pitch_hz > 160:
            gender_prediction = "Female"
        elif median_pitch_hz > 175:
            gender_prediction = "Female"
        else:
            gender_prediction = "Male"
        # --- END NEW LOGIC ---

        graph_times = downsample_array(times, target_points=150)
        graph_pitch_hz = downsample_array(f0, target_points=150)
        graph_pitch_midi = [round(p, 2) if p > 0 else None for p in librosa.hz_to_midi(graph_pitch_hz)]

        result = {
            "summary": {
                "duration_sec": duration,
                "percent_voiced": np.sum(voiced_flag) / len(voiced_flag) * 100,
                "gender_prediction": gender_prediction,
                # --- UPDATED: More accurate prediction note ---
                "prediction_note": "This is a probabilistic estimate based on pitch distribution analysis."
            },
            "pitch_details": {
                "average_pitch_hz": avg_pitch_hz,
                "pitch_std_dev_hz": np.nanstd(voiced_f0),
                "lowest_pitch_hz": min_pitch_hz,
                "highest_pitch_hz": max_pitch_hz,
                "vocal_range_semitones": librosa.hz_to_midi(max_pitch_hz) - librosa.hz_to_midi(min_pitch_hz),
                "lowest_note": librosa.hz_to_note(min_pitch_hz),
                "highest_note": librosa.hz_to_note(max_pitch_hz),
            },
            "loudness_details": {
                "average_loudness_db": avg_loudness_db,
                "loudness_variation_db": loudness_variation_db,
            },
            "vocal_quality": {
                "jitter_percent": jitter_local,
                "shimmer_percent": shimmer_local,
                "harmonics_to_noise_ratio_db": hnr,
            },
            "timbre_and_texture": {
                "spectral_centroid_hz": avg_spectral_centroid,
                "spectral_bandwidth_hz": avg_spectral_bandwidth,
                "zero_crossing_rate": avg_zero_crossing_rate,
            },
            "rhythm_and_rate": {
                "speech_rate_onsets_per_sec": speech_rate_onsets_sec
            },
            "performance_graph": {
                "timestamps": list(graph_times),
                "values": graph_pitch_midi,
                "value_type": "midi_note"
            }
        }
        return to_py_native(round_floats(result))

    except Exception as e:
        return {"error": f"Could not process vocals for '{audio_path}': {e}"}

# --- Refined Bass Analysis ---
def extract_bass_analytics(audio_path: str) -> dict:
    """
    Extracts summary metrics and a downsampled energy graph for bass.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration_sec = librosa.get_duration(y=y, sr=sr)
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        rhythm_stability = np.std(np.diff(onsets)) if len(onsets) > 1 else 0
        chromagram = librosa.feature.chroma_cqt(y=y, sr=sr)
        dominant_note_index = np.argmax(np.mean(chromagram, axis=1))
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.times_like(rms, sr=sr)
        graph_times = downsample_array(times, target_points=150)
        graph_values = downsample_array(rms, target_points=150)

        result = {
            "rhythm_stability": round(float(rhythm_stability), 2),
            "onset_density": round(len(onsets) / duration_sec, 2) if duration_sec > 0 else 0,
            "dominant_note": note_names[dominant_note_index],
            "low_end_power": round(float(np.mean(rms)), 2),
            "performance_graph": {
                "timestamps": [round(float(t), 2) for t in graph_times],
                "values": [round(float(v), 2) for v in graph_values],
                "value_type": "rms_energy"
            }
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process bass: {e}"}

# --- Refined Drums Analysis ---
def extract_drums_analytics(audio_path: str) -> dict:
    """
    Extracts summary metrics and a downsampled energy graph for drums.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
        groove_consistency = np.std(np.diff(beats)) if len(beats) > 1 else 0
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        kick_energy = np.sum(spectral_centroid < 150)
        snare_cymbal_energy = np.sum(spectral_centroid >= 150)
        
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.times_like(rms, sr=sr)
        graph_times = downsample_array(times, target_points=150)
        graph_values = downsample_array(rms, target_points=150)

        result = {
            "tempo_bpm": round(float(tempo), 2),
            "groove_consistency": round(float(groove_consistency), 2),
            "kick_to_snare_ratio": round(kick_energy / (snare_cymbal_energy + 1e-6), 2),
            "performance_graph": {
                "timestamps": [round(float(t), 2) for t in graph_times],
                "values": [round(float(v), 2) for v in graph_values],
                "value_type": "rms_energy"
            }
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process drums: {e}"}

# --- Refined Piano Analysis ---
def extract_piano_analytics(audio_path: str) -> dict:
    """
    Extracts summary metrics and a downsampled energy graph for piano.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.times_like(rms, sr=sr)
        graph_times = downsample_array(times, target_points=150)
        graph_values = downsample_array(rms, target_points=150)
        
        result = {
            "average_loudness": round(float(np.mean(rms)), 2),
            "dynamic_variation": round(float(np.std(rms)), 2),
            "average_brightness": round(float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0])), 2),
            "harmonic_complexity": round(float(np.mean(librosa.feature.spectral_flatness(y=y))), 2),
            "performance_graph": {
                "timestamps": [round(float(t), 2) for t in graph_times],
                "values": [round(float(v), 2) for v in graph_values],
                "value_type": "rms_energy"
            }
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process piano: {e}"}

# --- Refined Other Analysis ---
def extract_other_analytics(audio_path: str) -> dict:
    """
    Extracts summary metrics and a downsampled energy graph for other instruments.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.times_like(rms, sr=sr)
        graph_times = downsample_array(times, target_points=150)
        graph_values = downsample_array(rms, target_points=150)

        result = {
            "average_loudness": round(float(np.mean(rms)), 2),
            "average_brightness": round(float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0])), 2),
            "texture_complexity": round(float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)[0])), 2),
            "performance_graph": {
                "timestamps": [round(float(t), 2) for t in graph_times],
                "values": [round(float(v), 2) for v in graph_values],
                "value_type": "rms_energy"
            }
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process other stem: {e}"}

# --- Refined Guitar Analysis ---
def extract_guitar_analytics(audio_path: str) -> dict:
    """
    Extracts deep analytics and a performance graph for an isolated guitar track.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration_sec = librosa.get_duration(y=y, sr=sr)
        if duration_sec < 1.0:
            return {"error": "Audio is too short for meaningful guitar analysis."}

        # --- Rhythm & Harmony Analysis ---
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # --- Playing Style & "String Data" Interpretation ---
        onset_diffs = np.diff(onsets, prepend=0)
        strum_count = np.sum(onset_diffs < 0.1) # Onsets < 100ms apart suggest a strum
        picking_count = len(onsets) - strum_count
        
        chord_complexity = np.mean(np.sum(chroma > 0.6, axis=0))
        if chord_complexity < 1.8:
            chord_style = "Single Notes / Melodic Riffs"
        elif chord_complexity < 3.5:
            chord_style = "Power Chords / Simple Harmony"
        else:
            chord_style = "Complex / Full Voiced Chords"
            
        # --- Timbre & Technique ---
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        attack_noisiness = np.mean(librosa.feature.zero_crossing_rate(y=y_percussive))
        sustain_factor = 1 - np.mean(librosa.feature.spectral_flatness(y=y))
        
        # --- Graphing Data ---
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.times_like(rms, sr=sr)

        result = {
            "rhythm": {
                "estimated_tempo_bpm": round(float(tempo), 2),
                "strums_per_second": round(strum_count / duration_sec, 2),
                "picks_per_second": round(picking_count / duration_sec, 2),
            },
            "harmony_and_style": {
                "clarity_harmonic_ratio": round(np.sum(y_harmonic**2) / (np.sum(y**2) + 1e-7), 3),
                "chord_style_prediction": chord_style,
                "estimated_chord_complexity": round(float(chord_complexity), 3),
            },
            "technique": {
                "attack_noisiness": round(float(attack_noisiness), 4),
                "sustain_factor": round(float(sustain_factor), 3),
                "dynamic_variation": round(float(np.std(rms)), 3),
                "brightness_spectral_centroid": round(float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))), 2),
                "richness_spectral_bandwidth": round(float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))), 2),
            },
            "performance_graph": {
                "timestamps": [round(t, 2) for t in downsample_array(times, 150)],
                "values": [round(v, 3) for v in downsample_array(rms, 150)],
                "value_type": "rms_energy"
            }
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process for guitar: {e}"}
    
    
def _extract_melodic_instrument_data(audio_path: str, instrument_name: str, fmin: float, fmax: float) -> dict:
    """
    Extracts deep analytics for an isolated melodic instrument track. (Corrected Version)
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        f0, voiced_flag, _ = librosa.pyin(y, fmin=fmin, fmax=fmax)
        voiced_f0 = f0[voiced_flag]

        if len(voiced_f0) < 10: # Increased minimum length for stability
            return {"error": f"Could not detect a clear melody for {instrument_name}."}

        # --- Pitch & Melody ---
        pitch_range_semitones = librosa.hz_to_midi(np.max(voiced_f0)) - librosa.hz_to_midi(np.min(voiced_f0))

        # --- Vibrato Analysis (Corrected Logic) ---
        vibrato_rate_hz = 0
        vibrato_depth_cents = 0
        d_cents = np.diff(librosa.hz_to_midi(voiced_f0) * 100)
        
        if len(d_cents) > 0:
            vibrato_depth_cents = np.std(d_cents)
            
            # FFT settings for vibrato analysis on the pitch contour
            N_FFT_VIBRATO = 1024
            # The "sampling rate" of the f0 contour is the audio sample rate divided by the hop length
            f0_sr = sr / 512 # Default hop_length for pyin is 512

            # Perform STFT on the pitch contour only if there's enough data
            if len(d_cents) > N_FFT_VIBRATO:
                D = librosa.stft(np.pad(d_cents, N_FFT_VIBRATO//2) - np.mean(d_cents), n_fft=N_FFT_VIBRATO)
                fft_freqs = librosa.fft_frequencies(sr=f0_sr, n_fft=N_FFT_VIBRATO)
                vibrato_rate_hz = fft_freqs[np.argmax(np.mean(np.abs(D), axis=1))]

        # --- Articulation & Timbre ---
        legato_score = np.sum(voiced_flag) / len(voiced_flag)
        attack_clarity = np.mean(librosa.onset.onset_strength(y=y, sr=sr))
        h, p = librosa.effects.hpss(y)
        hnr = 10 * np.log10(np.sum(h**2) / (np.sum(p**2) + 1e-7)) if np.any(p) else 50.0
        breathiness_factor = np.mean(librosa.feature.spectral_flatness(y=y))

        # --- Graphing Data ---
        f0[~voiced_flag] = np.nan
        times = librosa.times_like(f0, sr=sr)

        result = {
            "pitch": {
                "average_pitch_hz": float(np.mean(voiced_f0)),
                "pitch_stability_hz_std": float(np.std(voiced_f0)),
                "pitch_range_semitones": float(pitch_range_semitones),
            },
            "vibrato": {
                "vibrato_rate_hz": float(vibrato_rate_hz),
                "vibrato_depth_cents": float(vibrato_depth_cents),
            },
            "articulation_and_timbre": {
                "legato_score": float(legato_score),
                "attack_clarity": float(attack_clarity),
                "harmonics_to_noise_ratio_db": float(hnr),
                "breathiness_or_scratchiness": float(breathiness_factor),
                "brightness_spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
            },
            "performance_graph": {
                "timestamps": [round(t, 2) for t in downsample_array(times, 150)],
                "values": [round(p, 2) if p > 0 else None for p in downsample_array(f0, 150)],
                "value_type": "pitch_hz"
            }
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process for {instrument_name}: {e}"}

def extract_violin_analytics(audio_path: str) -> dict:
    """
    Extracts summary and graph data for an isolated violin track.
    """
    return _extract_melodic_instrument_data(
        audio_path, "violin", 
        fmin=librosa.note_to_hz('G3'), 
        fmax=librosa.note_to_hz('A7')
    )

def extract_flute_analytics(audio_path: str) -> dict:
    """
    Extracts summary and graph data for an isolated flute track.
    """
    return _extract_melodic_instrument_data(
        audio_path, "flute", 
        fmin=librosa.note_to_hz('C4'), 
        fmax=librosa.note_to_hz('D7')
    )