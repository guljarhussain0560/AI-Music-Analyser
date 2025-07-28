import os
import time
import uuid
import tempfile
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import json
from requests import Session
from app.dto import schemas
from app.services import crud, s3_uploader
from app.utils import downloader, extract_analytics, spleeter_wrapper, parallel_processor

def find_audio_file(directory_path: str) -> str | None:
    """
    Scans a directory to find the first audio file.
    This handles cases where the downloader saves the file with a unique name.
    """
    if not os.path.isdir(directory_path):
        return directory_path if os.path.isfile(directory_path) else None
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.webm')):
            return os.path.join(directory_path, filename)
    return None

def process_and_upload_stem(wav_path: str, mp3_dir: str, s3_session_id: str) -> tuple[str, str] | None:
    """Converts a single WAV stem to MP3 and uploads it to S3."""
    if not os.path.exists(wav_path):
        # This warning is expected if spleeter doesn't generate a specific stem
        return None

    file_name_no_ext = os.path.basename(wav_path).replace('.wav', '')
    mp3_path = os.path.join(mp3_dir, f"{file_name_no_ext}.mp3")
    
    sound = AudioSegment.from_wav(wav_path)
    sound.export(mp3_path, format="mp3")
    
    s3_object_name = f"stems/{s3_session_id}/{file_name_no_ext}.mp3"
    s3_url = s3_uploader.upload_file_to_s3(mp3_path, object_name=s3_object_name)
    
    if s3_url:
        print(f"   -> Processed and uploaded {file_name_no_ext}.mp3")
        return file_name_no_ext, s3_url
    else:
        print(f"   -> Error uploading {file_name_no_ext}.mp3")
        return None

def full_song_processing_pipeline(db: Session, source_url: str, user_id: int):
    """
    Orchestrates the full pipeline, automatically selecting the correct downloader
    based on the source URL (YouTube or Spotify).
    """
    start_time = time.time()
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"✅ Created temporary directory: {temp_dir}")
            
            # --- 1. Download ---
            output_location = os.path.join(temp_dir, "original_song")
            original_title = ""

            print(f"Detecting source for URL: {source_url}")
            if "youtube.com" in source_url or "youtu.be" in source_url:
                original_title = downloader.download_from_youtube(source_url, output_location)
            else: # Simplified for brevity
                original_title = downloader.download_from_spotify(source_url, output_location)
            
            original_audio_path = find_audio_file(output_location)
            if not original_audio_path:
                raise FileNotFoundError(f"Could not find downloaded audio file in {output_location}")
            
            print(f"✅ Downloaded '{original_title}' to {original_audio_path}")
            
            # --- 2. Parallel Processing (Upload, Analyze, Split) ---
            s3_upload_url = None
            music_desc = None
            stems_output_dir = os.path.join(temp_dir, "stems")
            os.makedirs(stems_output_dir)

            print("🚀 Starting parallel processing: Uploading, Analyzing, and Splitting...")
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit tasks to run in parallel
                s3_upload_future = executor.submit(s3_uploader.upload_file_to_s3, original_audio_path, f"songs/{user_id}/{original_title}.mp3")
                analytics_future = executor.submit(extract_analytics.extract_music_analytics, original_audio_path)
                spleeter_future = executor.submit(spleeter_wrapper.spleeter_5_stem_split, original_audio_path, stems_output_dir)

                # Retrieve results as they complete
                s3_upload_url = s3_upload_future.result()
                print("✅ Original song uploaded to S3.")
                
                music_desc = analytics_future.result()
                print("✅ Initial audio analysis complete.")

                # Wait for the longest task (spleeter) to finish
                spleeter_future.result()
                print(f"✅ Audio split into stems in {stems_output_dir}")

            # --- 3. Create Initial DB Record ---
            song_data_dto = schemas.SongCreateDTO(
                title=original_title, owner_id=user_id, song_url=s3_upload_url,
                lyrics={}, description=music_desc
            )
            new_song = crud.create_song(db=db, song=song_data_dto)
            print(f"✅ Saved initial song record with ID: {new_song.id}")
            
            # --- 4. Process Stems in Parallel ---
            conv_mp3_dir = os.path.join(temp_dir, "stems_mp3")
            os.makedirs(conv_mp3_dir, exist_ok=True)
            stem_names = ["vocals", "bass", "drums", "piano", "other"]
            session_id = uuid.uuid4()
            s3_urls = {}

            input_filename_stem = os.path.splitext(os.path.basename(original_audio_path))[0]
            spleeter_output_subdir = os.path.join(stems_output_dir, input_filename_stem)
            stem_paths_to_process = [os.path.join(spleeter_output_subdir, f"{name}.wav") for name in stem_names]

            print("🎵 Converting and uploading stems in parallel...")
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_stem = {executor.submit(process_and_upload_stem, path, conv_mp3_dir, session_id): path for path in stem_paths_to_process}
                for future in as_completed(future_to_stem):
                    result = future.result()
                    if result:
                        s3_urls[result[0]] = result[1]
            
            print(f"✅ All available stems processed and uploaded.")
            vocal_url, bass_url, drums_url, piano_url, other_url = (
                s3_urls.get("vocals"), s3_urls.get("bass"), s3_urls.get("drums"),
                s3_urls.get("piano"), s3_urls.get("other")
            )

            # --- 5. Final Parallel Analysis and DB Record ---
            print("Starting final parallel audio analysis...")
            all_7_data = parallel_processor.run_analysis_in_parallel(spleeter_output_subdir)
            
            vocal_data, bass_data, drums_data, piano_data, other_data, guitar_data, violin_data, flute_data = (
                all_7_data.get("vocal"), all_7_data.get("bass"), all_7_data.get("drums"),
                all_7_data.get("piano"), all_7_data.get("other"), all_7_data.get("guitar"),
                all_7_data.get("violin"), all_7_data.get("flute")
            )
            
            split_data_dto = schemas.SplitCreateDTO(
                song_id=new_song.id,
                bass_audio_url=bass_url, bass_description=bass_data,
                vocals_audio_url=vocal_url, vocals_description=vocal_data,
                piano_audio_url=piano_url, piano_description=piano_data,
                other_audio_url=other_url, other_description=other_data,
                drum_audio_url=drums_url, drum_description=drums_data,
                guitar_description=guitar_data,
                violin_description=violin_data,
                flute_description=flute_data
            )
            new_split_record = crud.create_split(db=db, split=split_data_dto)
            print(f"✅ Successfully created database record with ID: {new_split_record.id}")

            print(f"✅ DONE. Temporary directory {temp_dir} and all its contents were automatically deleted. 🗑️")
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"⏱️ Total processing time: {elapsed_time:.2f} seconds")
            return {
                "songs_id": new_song.id,
                "splits_id": new_split_record.id,
            }

    except Exception as e:
        print(f"❌ An error occurred during the pipeline: {e}")
        if 'db' in locals() and db.is_active:
            db.rollback()
        return None
