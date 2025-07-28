import os
import librosa
import numpy as np
from sklearn.preprocessing import minmax_scale

def extract_music_analytics(audio_path: str, is_vocal_track: bool = False) -> dict:
    """
    Performs a highly detailed analysis of a music file to extract a compact,
    interpretable summary for a frontend dashboard.

    :param audio_path: Path to the local audio file.
    :param is_vocal_track: Set to True if the track is vocals-only to tailor analysis.
    :return: A compact dictionary of high-level music analytics.
    """
    print(f"📈 Performing advanced analysis for dashboard on: {audio_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at: {audio_path}")

    try:
        # Load audio at a standard sample rate
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)

        # --- Main Information & Details ---
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='frames')
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        key_index = np.argmax(chroma_mean)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        # Calculate tempo variations across 5 segments
        segment_duration = duration / 5
        tempo_variations = [librosa.beat.beat_track(y=y[int(i*segment_duration*sr):int((i+1)*segment_duration*sr)], sr=sr)[0] for i in range(5)]

        main_information = {
            "bpm": round(float(tempo), 1),
            "key": keys[key_index],
            "details": {
                "bpm_confidence": float(tempo),
                "tempo_variations": [round(float(t), 2) for t in tempo_variations],
                "key_confidence": round(float(np.max(chroma_mean) / np.sum(chroma_mean)), 4),
                "chroma_profile": [round(float(val), 4) for val in minmax_scale(chroma_mean)],
                "harmonic_ratio": round(float(np.mean(librosa.feature.rms(y=y_harmonic)[0]) / (np.mean(librosa.feature.rms(y=y)[0]) + 1e-6)), 4),
                "percussive_ratio": round(float(np.mean(librosa.feature.rms(y=y_percussive)[0]) / (np.mean(librosa.feature.rms(y=y)[0]) + 1e-6)), 4),
                "spectral_centroid_mean": round(float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))), 4),
                "spectral_bandwidth_mean": round(float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))), 4),
                "spectral_rolloff_mean": round(float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))), 4),
                "zero_crossing_rate_mean": round(float(np.mean(librosa.feature.zero_crossing_rate(y))), 4),
                "dynamic_range": round(float(np.mean(librosa.feature.spectral_contrast(y=y, sr=sr))), 4),
                "total_onsets": int(len(onsets)),
                "onset_density": round(len(onsets) / duration, 4) if duration > 0 else 0,
                "duration_seconds": round(duration, 2)
            }
        }

        # --- Audio Quality ---
        rms_level = np.mean(librosa.feature.rms(y=y)[0])
        peak_amplitude = np.max(np.abs(y))
        audio_quality = {
            "sample_rate": int(sr),
            "peak_amplitude": round(float(peak_amplitude), 4),
            "rms_level": round(float(rms_level), 4),
            "crest_factor": round(float(peak_amplitude / (rms_level + 1e-6)), 4),
            "snr_estimate": round(float(10 * np.log10(np.mean(y**2) / (np.var(y) + 1e-6))), 2),
            "clipping_ratio": round(float((np.sum(np.abs(y) >= 0.99) / len(y)) * 100), 4),
            "bit_depth_estimate": 16 # Placeholder
        }

        # --- Genre & Mood (Placeholder) ---
        genre_and_mood = {
            "main_genre": "Bollywood", "sub_genres": ["Desi Pop"], "genre_confidence": 0.75,
            "moods": [{"name": "Happy", "score": 0.44}, {"name": "Romantic", "score": 0.38}],
            "tempo_based_mood": "Medium" if 90 <= tempo <= 140 else "Fast" if tempo > 140 else "Slow"
        }

        # --- Vocal or Instrument Analysis ---
        analysis_section = {}
        if is_vocal_track:
            f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            f0_voiced = f0[voiced_flag]
            gender = "Female" if np.nanmedian(f0_voiced) > 165 else "Male" if np.nanmedian(f0_voiced) else "Unknown"
            analysis_section["vocal_analysis"] = {
                "presence": "High", "gender": gender,
                "details": {
                    "f0_median": round(float(np.nanmedian(f0_voiced)), 2) if len(f0_voiced) > 0 else 0,
                    "f0_std": round(float(np.nanstd(f0_voiced)), 2) if len(f0_voiced) > 0 else 0,
                    "vibrato_detected": bool(np.nanstd(f0_voiced) > 15) if len(f0_voiced) > 0 else False,
                    "gender_confidence": round(float(np.mean(voiced_probs)), 2) if len(voiced_probs) > 0 else 0
                }
            }

        # --- Final Combined Dictionary ---
        final_analytics = {
            "main_information": main_information,
            "audio_quality": audio_quality,
            "genre_and_mood": genre_and_mood,
            **analysis_section
        }

        print("✅ Advanced analysis complete.")
        return final_analytics

    except Exception as e:
        print(f"❌ An error occurred during advanced audio analysis: {e}")
        return {"error": str(e)}


    
    

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

# --- Refined Vocal Analysis ---
def extract_vocal_analytics(audio_path: str) -> dict:
    """
    Extracts high-level, meaningful metrics about the vocal performance.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        
        voiced_f0 = f0[voiced_flag]
        pitch_mean_hz = np.nanmean(voiced_f0) if len(voiced_f0) > 0 else 0
        pitch_std_hz = np.nanstd(voiced_f0) if len(voiced_f0) > 0 else 0

        result = {
            "info": "High-level summary of vocal characteristics.",
            "average_pitch_hz": round(pitch_mean_hz, 2),
            "pitch_variation_hz": round(pitch_std_hz, 2), # Represents vibrato and pitch movement
            "range_semitones": round(librosa.hz_to_midi(np.nanmax(voiced_f0)) - librosa.hz_to_midi(np.nanmin(voiced_f0)), 2) if len(voiced_f0) > 1 else 0,
            "percent_voiced": round(np.sum(voiced_flag) / len(voiced_flag) * 100, 2)
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process vocals: {e}"}

# --- Refined Bass Analysis ---
def extract_bass_analytics(audio_path: str) -> dict:
    """
    Extracts high-level, meaningful metrics about the bassline's performance.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration_sec = librosa.get_duration(y=y, sr=sr)
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        
        # Rhythmic stability: Lower std means more stable rhythm
        rhythm_stability = np.std(np.diff(onsets)) if len(onsets) > 1 else 0
        
        chromagram = librosa.feature.chroma_cqt(y=y, sr=sr)
        dominant_note_index = np.argmax(np.mean(chromagram, axis=1))
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        result = {
            "info": "Summary of the bassline's rhythmic and harmonic role.",
            "rhythm_stability": round(rhythm_stability, 4),
            "onset_density": round(len(onsets) / duration_sec, 4) if duration_sec > 0 else 0,
            "dominant_note": note_names[dominant_note_index],
            "low_end_power": round(np.mean(librosa.feature.rms(y=y)[0]), 4)
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process bass: {e}"}

# --- Refined Drums Analysis ---
def extract_drums_analytics(audio_path: str) -> dict:
    """
    Extracts high-level, meaningful metrics about the drum pattern.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
        
        # Groove consistency: Lower std means a more steady beat
        groove_consistency = np.std(np.diff(beats)) if len(beats) > 1 else 0
        
        # Estimate kick vs. snare/cymbal energy
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        kick_energy = np.sum(spectral_centroid < 150) # Energy in low frequencies
        snare_cymbal_energy = np.sum(spectral_centroid >= 150) # Energy in higher frequencies

        result = {
            "info": "Summary of the drum pattern's tempo and character.",
            "tempo_bpm": round(tempo, 2),
            "groove_consistency": round(groove_consistency, 4),
            "kick_to_snare_ratio": round(kick_energy / (snare_cymbal_energy + 1e-6), 2)
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process drums: {e}"}

# --- Refined Piano Analysis ---
def extract_piano_analytics(audio_path: str) -> dict:
    """
    Extracts high-level, meaningful metrics about the piano performance.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        
        # Harmonic complexity (lower flatness = more tonal/less noisy)
        harmonic_complexity = np.mean(librosa.feature.spectral_flatness(y=y))
        
        result = {
            "info": "Summary of the piano's dynamics, timbre, and complexity.",
            "average_loudness": round(np.mean(librosa.feature.rms(y=y)[0]), 4),
            "dynamic_variation": round(np.std(librosa.feature.rms(y=y)[0]), 4),
            "average_brightness": round(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0]), 2),
            "harmonic_complexity": round(harmonic_complexity, 4)
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process piano: {e}"}

# --- Refined Other Analysis ---
def extract_other_analytics(audio_path: str) -> dict:
    """
    Extracts a general-purpose summary for the 'other' instruments stem.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        result = {
            "info": "General summary for the mixed 'other' stem.",
            "average_loudness": round(np.mean(librosa.feature.rms(y=y)[0]), 4),
            "average_brightness": round(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)[0]), 2),
            "texture_complexity": round(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]), 2)
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process other stem: {e}"}

# --- Refined Guitar Analysis ---
def extract_guitar_analytics(audio_path: str) -> dict:
    """
    Extracts high-level, meaningful metrics about the guitar performance.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        duration_sec = librosa.get_duration(y=y, sr=sr)
        
        # Estimate if it's more rhythmic (percussive) or melodic (harmonic)
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_ratio = np.sum(y_harmonic**2) / (np.sum(y**2) + 1e-6)

        result = {
            "info": "Summary of guitar characteristics like rhythm and harmony.",
            "strum_density": round(len(onsets) / duration_sec, 4) if duration_sec > 0 else 0,
            "dynamic_variation": round(np.std(librosa.feature.rms(y=y)[0]), 4),
            "harmonic_clarity": round(harmonic_ratio, 4), # Higher means more tonal/melodic
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process for guitar: {e}"}

# --- Refined Melodic Instrument Analysis (Violin and Flute) ---
def _extract_melodic_instrument_data(audio_path: str, instrument_name: str, fmin: float, fmax: float) -> dict:
    """
    A generic helper to extract a high-level summary for melodic instruments.
    """
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        f0, voiced_flag, _ = librosa.pyin(y, fmin=fmin, fmax=fmax)
        voiced_f0 = f0[voiced_flag]
        
        # How much the melody jumps around
        pitch_stability = np.nanstd(np.diff(voiced_f0)) if len(voiced_f0) > 1 else 0

        result = {
            "info": f"Summary of melodic characteristics for {instrument_name}.",
            "average_pitch_hz": round(np.nanmean(voiced_f0), 2) if len(voiced_f0) > 0 else 0,
            "pitch_stability_hz": round(pitch_stability, 2), # Lower is more stable/less jumpy
            "average_loudness": round(np.mean(librosa.feature.rms(y=y)[0]), 4)
        }
        return to_py_native(result)
    except Exception as e:
        return {"error": f"Could not process for {instrument_name}: {e}"}

def extract_violin_analytics(audio_path: str) -> dict:
    """
    Extracts a high-level summary for a violin by analyzing its typical pitch range.
    """
    return _extract_melodic_instrument_data(
        audio_path, "violin", fmin=librosa.note_to_hz('G3'), fmax=librosa.note_to_hz('A7')
    )

def extract_flute_analytics(audio_path: str) -> dict:
    """
    Extracts a high-level summary for a flute by analyzing its typical pitch range.
    """
    return _extract_melodic_instrument_data(
        audio_path, "flute", fmin=librosa.note_to_hz('C4'), fmax=librosa.note_to_hz('D7')
    )

