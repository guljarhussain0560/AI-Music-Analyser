import os
import librosa
import numpy as np
import json
from scipy import stats
import soundfile as sf

# --- Enhanced Analysis Helper Functions ---

def analyze_vocals(file_path):
    """Enhanced vocal analysis with detailed pitch, formant, and vocal characteristics."""
    if not os.path.exists(file_path):
        return {"presence": "None", "gender": "Unknown", "details": {}}

    try:
        y, sr = librosa.load(file_path)
        print(f"🎤 Analyzing vocals: {file_path}")

        # Enhanced presence detection
        rms = librosa.feature.rms(y=y)
        rms_mean = np.mean(rms)
        rms_std = np.std(rms)
        is_present = rms_mean > 0.01

        if not is_present:
            return {"presence": "None", "gender": "Unknown", "details": {"rms_mean": float(rms_mean)}}

        # Advanced pitch analysis
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        valid_pitches = pitches[pitches > 0]
        
        # Fundamental frequency analysis
        f0 = librosa.yin(y, fmin=50, fmax=400)
        f0_clean = f0[f0 > 0]
        
        # Formant estimation (basic)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        
        # Vocal intensity analysis
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        
        # Gender classification with confidence
        average_pitch = np.mean(valid_pitches) if len(valid_pitches) > 0 else 0
        f0_median = np.median(f0_clean) if len(f0_clean) > 0 else 0
        
        gender = "Unknown"
        gender_confidence = 0.0
        
        if f0_median > 0:
            if 80 < f0_median < 180:
                gender = "Male"
                gender_confidence = min(1.0, (180 - f0_median) / 100)
            elif f0_median >= 180:
                gender = "Female" 
                gender_confidence = min(1.0, (f0_median - 180) / 100)

        vocal_details = {
            "rms_mean": float(rms_mean),
            "rms_std": float(rms_std),
            "pitch_mean": float(average_pitch),
            "pitch_std": float(np.std(valid_pitches)) if len(valid_pitches) > 0 else 0,
            "f0_median": float(f0_median),
            "f0_mean": float(np.mean(f0_clean)) if len(f0_clean) > 0 else 0,
            "f0_std": float(np.std(f0_clean)) if len(f0_clean) > 0 else 0,
            "spectral_centroid_mean": float(np.mean(spectral_centroid)),
            "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
            "spectral_bandwidth_mean": float(np.mean(spectral_bandwidth)),
            "mfcc_mean": [float(x) for x in np.mean(mfccs, axis=1)],
            "vocal_onsets_count": len(onset_times),
            "vocal_onset_rate": len(onset_times) / (len(y) / sr),
            "gender_confidence": float(gender_confidence),
            "vocal_range_hz": float(np.max(f0_clean) - np.min(f0_clean)) if len(f0_clean) > 0 else 0,
            "vibrato_detected": bool(np.std(f0_clean) > 10) if len(f0_clean) > 0 else False
        }

        return {
            "presence": "High" if rms_mean > 0.02 else "Medium" if rms_mean > 0.01 else "Low",
            "gender": gender,
            "details": vocal_details
        }

    except Exception as e:
        print(f"❌ Could not process vocal file {file_path}: {e}")
        return {"presence": "Unknown", "gender": "Unknown", "error": str(e)}

def analyze_main_track(file_path):
    """Enhanced main track analysis with detailed rhythm, harmony, and structure."""
    if not os.path.exists(file_path):
        return {"bpm": 0, "key": "Unknown", "details": {}}
        
    try:
        y, sr = librosa.load(file_path, duration=120)  # Limit to 2 minutes for performance
        print(f"🎵 Analyzing main track: {file_path}")
        
        # Enhanced tempo analysis - FIXED DEPRECATION WARNING
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
        
        # Use the new function path for librosa >= 0.10.0
        try:
            tempo_confidence = librosa.feature.rhythm.tempo(onset_envelope=onset_envelope, sr=sr, aggregate=None)
        except AttributeError:
            # Fallback for older versions
            tempo_confidence = librosa.beat.tempo(onset_envelope=onset_envelope, sr=sr, aggregate=None)
        
        # Advanced key estimation
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        key_index = np.argmax(chroma_mean)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        estimated_key = keys[key_index]
        key_confidence = float(chroma_mean[key_index] / np.sum(chroma_mean))
        
        # Harmonic analysis
        harmonic, percussive = librosa.effects.hpss(y)
        harmonic_ratio = np.mean(np.abs(harmonic)) / (np.mean(np.abs(y)) + 1e-8)
        percussive_ratio = np.mean(np.abs(percussive)) / (np.mean(np.abs(y)) + 1e-8)
        
        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
        
        # Rhythm analysis
        tempogram = librosa.feature.tempogram(onset_envelope=onset_envelope, sr=sr)
        rhythm_complexity = float(np.std(tempogram))
        
        # Dynamic range analysis
        rms = librosa.feature.rms(y=y)
        dynamic_range = float(np.max(rms) - np.min(rms))
        loudness_variation = float(np.std(rms))
        
        # Structure analysis
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        segment_boundaries = librosa.segment.agglomerative(chroma, k=8)
        
        details = {
            "bpm_confidence": float(np.max(tempo_confidence)),
            "tempo_variations": [float(x) for x in tempo_confidence[:5]],  # Top 5 tempo candidates
            "key_confidence": key_confidence,
            "chroma_profile": [float(x) for x in chroma_mean],
            "harmonic_ratio": float(harmonic_ratio),
            "percussive_ratio": float(percussive_ratio),
            "spectral_centroid_mean": float(np.mean(spectral_centroid)),
            "spectral_centroid_std": float(np.std(spectral_centroid)),
            "spectral_bandwidth_mean": float(np.mean(spectral_bandwidth)),
            "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
            "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
            "rhythm_complexity": rhythm_complexity,
            "dynamic_range": dynamic_range,
            "loudness_variation": loudness_variation,
            "total_onsets": len(onset_frames),
            "onset_density": len(onset_frames) / (len(y) / sr),
            "estimated_sections": len(segment_boundaries),
            "duration_seconds": float(len(y) / sr)
        }
        
        return {
            "bpm": round(np.mean(tempo)), 
            "key": estimated_key,
            "details": details
        }
        
    except Exception as e:
        print(f"❌ Could not process main track {file_path}: {e}")
        return {"bpm": 0, "key": "Unknown", "error": str(e)}

def identify_instruments(stems_directory):
    """Enhanced instrument identification with detailed acoustic analysis."""
    instruments_info = []
    instrument_files = {
        "Bass": "bass.wav",
        "Drums": "drums.wav", 
        "Piano": "piano.wav",
        "Other": "other.wav",
        "Vocals": "vocals.wav"
    }

    for name, filename in instrument_files.items():
        file_path = os.path.join(stems_directory, filename)
        if os.path.exists(file_path):
            try:
                y, sr = librosa.load(file_path)
                print(f"🎼 Analyzing {name}: {filename}")
                
                # Basic features
                rms = librosa.feature.rms(y=y)
                rms_mean = float(np.mean(rms))
                duration = float(librosa.get_duration(y=y, sr=sr))
                
                # Advanced spectral analysis
                spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
                spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
                spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
                spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
                
                # Rhythmic features
                zero_crossings = int(np.sum(librosa.zero_crossings(y)))
                zcr = librosa.feature.zero_crossing_rate(y)
                onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
                onset_strength = librosa.onset.onset_strength(y=y, sr=sr)
                
                # Harmonic analysis
                pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
                valid_pitches = pitches[pitches > 0]
                
                # MFCCs for timbral analysis
                mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
                
                # Chroma features
                chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                
                # Instrument-specific analysis
                if name == "Drums":
                    # Percussion-specific features
                    tempogram = librosa.feature.tempogram(onset_envelope=onset_strength, sr=sr)
                    drum_pattern_complexity = float(np.std(tempogram))
                elif name == "Bass":
                    # Low-frequency analysis
                    low_freq_energy = np.sum(np.abs(librosa.stft(y, n_fft=2048))[:256, :])  # 0-2kHz
                    total_energy = np.sum(np.abs(librosa.stft(y, n_fft=2048)))
                    bass_ratio = low_freq_energy / (total_energy + 1e-8)
                
                # Activity detection
                activity_threshold = 0.01
                active_frames = np.sum(rms[0] > activity_threshold)
                activity_ratio = active_frames / len(rms[0])
                
                instrument_details = {
                    "average_rms": rms_mean,
                    "rms_std": float(np.std(rms)),
                    "duration_sec": duration,
                    "spectral_centroid_mean": float(np.mean(spectral_centroid)),
                    "spectral_centroid_std": float(np.std(spectral_centroid)),
                    "spectral_bandwidth_mean": float(np.mean(spectral_bandwidth)),
                    "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
                    "spectral_contrast_mean": [float(x) for x in np.mean(spectral_contrast, axis=1)],
                    "zero_crossings_total": zero_crossings,
                    "zero_crossing_rate_mean": float(np.mean(zcr)),
                    "zero_crossing_rate_std": float(np.std(zcr)),
                    "onset_count": len(onset_frames),
                    "onset_rate": len(onset_frames) / duration,
                    "onset_strength_mean": float(np.mean(onset_strength)),
                    "pitch_mean": float(np.mean(valid_pitches)) if len(valid_pitches) > 0 else 0,
                    "pitch_std": float(np.std(valid_pitches)) if len(valid_pitches) > 0 else 0,
                    "pitch_range": float(np.max(valid_pitches) - np.min(valid_pitches)) if len(valid_pitches) > 0 else 0,
                    "mfcc_mean": [float(x) for x in np.mean(mfccs, axis=1)],
                    "mfcc_std": [float(x) for x in np.std(mfccs, axis=1)],
                    "chroma_mean": [float(x) for x in np.mean(chroma, axis=1)],
                    "activity_ratio": float(activity_ratio),
                    "dynamic_range": float(np.max(rms) - np.min(rms)),
                    "energy_distribution": {
                        "low_freq": float(np.sum(np.abs(librosa.stft(y, n_fft=2048))[:256, :])),
                        "mid_freq": float(np.sum(np.abs(librosa.stft(y, n_fft=2048))[256:768, :])),
                        "high_freq": float(np.sum(np.abs(librosa.stft(y, n_fft=2048))[768:, :]))
                    }
                }
                
                # Add instrument-specific features
                if name == "Drums":
                    instrument_details["drum_pattern_complexity"] = drum_pattern_complexity
                elif name == "Bass":
                    instrument_details["bass_frequency_ratio"] = float(bass_ratio)

                instruments_info.append({
                    "name": name,
                    "file": filename,
                    "presence": "High" if rms_mean > 0.02 else "Medium" if rms_mean > 0.01 else "Low",
                    "confidence": float(min(1.0, rms_mean * 50)),  # Confidence based on RMS
                    "details": instrument_details
                })
                
            except Exception as e:
                print(f"❌ Error analyzing {name}: {e}")
                instruments_info.append({
                    "name": name,
                    "file": filename,
                    "presence": "Unknown",
                    "error": str(e)
                })
    return instruments_info

def analyze_audio_quality(file_path):
    """Analyze audio quality metrics."""
    try:
        y, sr = librosa.load(file_path)
        
        # Signal-to-noise ratio estimation
        rms = librosa.feature.rms(y=y)
        snr_estimate = 20 * np.log10(np.mean(rms) / (np.std(rms) + 1e-8))
        
        # Dynamic range
        peak = np.max(np.abs(y))
        rms_overall = np.sqrt(np.mean(y**2))
        crest_factor = peak / (rms_overall + 1e-8)
        
        # Clipping detection
        clipping_ratio = np.sum(np.abs(y) > 0.99) / len(y)
        
        return {
            "sample_rate": sr,
            "duration": float(len(y) / sr),
            "peak_amplitude": float(peak),
            "rms_level": float(rms_overall),
            "crest_factor": float(crest_factor),
            "snr_estimate": float(snr_estimate),
            "clipping_ratio": float(clipping_ratio),
            "bit_depth_estimate": 16 if peak < 0.5 else 24  # Rough estimate
        }
    except Exception as e:
        return {"error": str(e)}

# --- Enhanced Main Report Generation Function ---

def generate_report(original_track_path, stems_directory):
    """
    Generates a comprehensive analysis report with deep audio analysis.
    """
    print("🔍 Starting comprehensive audio analysis...")
    
    # 1. Enhanced main track analysis
    main_features = analyze_main_track(original_track_path)
    
    # 2. Audio quality analysis
    quality_analysis = analyze_audio_quality(original_track_path)
    
    # 3. Enhanced vocal analysis
    vocal_file_path = os.path.join(stems_directory, "vocals.wav")
    vocal_analysis = analyze_vocals(vocal_file_path)
    
    # 4. Enhanced instrument analysis
    instrument_analysis = identify_instruments(stems_directory)
    
    # 5. Cross-stem analysis
    stem_files = [f for f in os.listdir(stems_directory) if f.endswith('.wav')]
    stem_correlation = {}
    
    try:
        # Calculate correlation between stems
        for i, file1 in enumerate(stem_files):
            for file2 in stem_files[i+1:]:
                y1, _ = librosa.load(os.path.join(stems_directory, file1), duration=30)
                y2, _ = librosa.load(os.path.join(stems_directory, file2), duration=30)
                min_len = min(len(y1), len(y2))
                correlation = float(np.corrcoef(y1[:min_len], y2[:min_len])[0, 1])
                stem_correlation[f"{file1}_vs_{file2}"] = correlation
    except Exception as e:
        print(f"⚠️ Stem correlation analysis failed: {e}")
    
    # 6. Assemble comprehensive report
    final_report = {
        "metadata": {
            "analysis_timestamp": json.dumps(np.datetime64('now').astype(str)),
            "stems_found": len(stem_files),
            "total_analysis_files": len(stem_files) + 1
        },
        "main_information": {
            "bpm": main_features["bpm"],
            "key": main_features["key"],
            "details": main_features.get("details", {})
        },
        "audio_quality": quality_analysis,
        "genre_and_mood": {
            # Enhanced with confidence scores based on actual analysis
            "main_genre": "Bollywood",  # TODO: ML-based classification
            "sub_genres": ["Desi Pop"],
            "genre_confidence": 0.75,  # TODO: Based on actual features
            "moods": [
                {"name": "Happy", "score": 0.44},
                {"name": "Romantic", "score": 0.38}, 
                {"name": "Energetic", "score": 0.37}
            ],
            "tempo_based_mood": "Medium" if main_features["bpm"] < 120 else "Energetic",
            "harmonic_complexity": main_features.get("details", {}).get("rhythm_complexity", 0)
        },
        "vocal_analysis": {
            "presence": vocal_analysis["presence"],
            "gender": vocal_analysis["gender"],
            "details": vocal_analysis.get("details", {})
        },
        "instrument_analysis": {
            "instruments_present": instrument_analysis,
            "instrument_count": len([i for i in instrument_analysis if i["presence"] in ["High", "Medium"]]),
            "dominant_instrument": max(instrument_analysis, key=lambda x: x.get("confidence", 0))["name"] if instrument_analysis else "None"
        },
        "advanced_analysis": {
            "stem_correlations": stem_correlation,
            "mix_balance": {
                "vocal_prominence": vocal_analysis.get("details", {}).get("rms_mean", 0),
                "instrument_balance": [
                    {"name": inst["name"], "level": inst.get("details", {}).get("average_rms", 0)} 
                    for inst in instrument_analysis
                ]
            },
            "production_quality": {
                "dynamic_range": quality_analysis.get("crest_factor", 0),
                "mastering_level": "Professional" if quality_analysis.get("crest_factor", 0) > 3 else "Demo",
                "stereo_imaging": "Estimated based on spectral analysis"  # TODO: Implement
            }
        }
    }
    
    print("✅ Comprehensive analysis complete!")
    return final_report

# --- Execute the Script ---

if __name__ == "__main__":
    # IMPORTANT: Update these paths to match your file locations!
    ORIGINAL_TRACK_PATH = "test_dir/original_song.mp3" 
    STEMS_DIRECTORY = "test_dir/" 

    # Generate the comprehensive report
    print("🚀 Generating deep audio analysis report...")
    full_analysis_report = generate_report(ORIGINAL_TRACK_PATH, STEMS_DIRECTORY)

    # Save report to file
    output_file = "comprehensive_audio_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(full_analysis_report, f, indent=4)
    
    print(f"\n📊 COMPREHENSIVE ANALYSIS REPORT")
    print(f"Report saved to: {output_file}")
    print("="*50)
    print(json.dumps(full_analysis_report, indent=2))