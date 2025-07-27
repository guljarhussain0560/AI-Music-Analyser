import librosa
import numpy as np
import os

def extract_music_analytics(audio_path: str) -> dict:
    """
    Analyzes an audio file and extracts detailed data for various frontend graphs.

    :param audio_path: Path to the local audio file.
    :return: A dictionary containing data for waveform, spectrogram, etc.
    """
    print(f"📈 Analyzing audio for graphs: {audio_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found at: {audio_path}")

    try:
        # Load the audio file, resample to a standard rate for consistency
        y, sr = librosa.load(audio_path, sr=22050)
        duration = librosa.get_duration(y=y, sr=sr)

        # --- Basic Summary Information ---
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma_stft, axis=1)
        key_index = np.argmax(chroma_mean)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        summary_data = {
            "duration": round(duration, 2),
            "bpm": round(float(tempo)),
            "key": keys[key_index],
            "key_confidence": float(chroma_mean[key_index] / np.sum(chroma_mean))
        }

        # --- Graph Data ---

        # 1. Waveform Data (Amplitude Envelope)
        rms = librosa.feature.rms(y=y)[0]
        times = librosa.times_like(rms, sr=sr)
        waveform_data = {
            "times": times.tolist(),
            "amplitude": rms.tolist()
        }

        # 2. Spectrogram Data (Frequency vs. Time)
        mel_spectrogram = librosa.feature.melspectrogram(y=y, sr=sr)
        db_spectrogram = librosa.power_to_db(mel_spectrogram, ref=np.max)
        spectrogram_data = {
            "times": librosa.times_like(db_spectrogram, sr=sr).tolist(),
            "frequencies": librosa.mel_frequencies(n_mels=db_spectrogram.shape[0], sr=sr).tolist(),
            "db_values": db_spectrogram.tolist()
        }
        
        # 3. Chromagram Data (Harmonic Content)
        chromagram_data = {
            "times": librosa.times_like(chroma_stft, sr=sr).tolist(),
            "notes": keys,
            "values": chroma_stft.tolist()
        }

        # 4. Harmonic and Percussive Components
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_rms = librosa.feature.rms(y=y_harmonic)[0]
        percussive_rms = librosa.feature.rms(y=y_percussive)[0]
        components_data = {
            "times": times.tolist(),
            "harmonic_amplitude": harmonic_rms.tolist(),
            "percussive_amplitude": percussive_rms.tolist()
        }

        # 5. Spectral Contrast (Texture)
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        spectral_contrast_data = {
            "times": librosa.times_like(spectral_contrast, sr=sr).tolist(),
            "frequency_bands": [f"Band {i+1}" for i in range(spectral_contrast.shape[0])],
            "values": spectral_contrast.tolist()
        }
        
        # 6. Rhythm and Structure Data
        # Use a subset of beats for a cleaner visualization of sections
        segment_frames = librosa.segment.agglomerative(chroma_stft, k=10)
        section_boundary_times = librosa.frames_to_time(segment_frames, sr=sr)
        rhythm_data = {
            "beat_times": beat_times.tolist(),
            "section_boundaries": section_boundary_times.tolist()
        }

        print("✅ Analysis complete.")
        return {
            "summary": summary_data,
            "waveform": waveform_data,
            "spectrogram": spectrogram_data,
            "chromagram": chromagram_data,
            "components": components_data,
            "texture": spectral_contrast_data,
            "rhythm": rhythm_data
        }

    except Exception as e:
        print(f"❌ An error occurred during audio analysis: {e}")
        return {"error": str(e)}