import tempfile
import os
import uuid
from pydub import AudioSegment

from flask import json
from requests import Session
from app.dto import schemas
from app.services import crud
from app.services import s3_uploader
from app.utils import downloader, extract_analytics
from app.utils import spleeter_wrapper
from app.utils import parallel_processor



def full_song_processing_pipeline(db: Session, source_url: str, user_id: int):
    """
    Orchestrates the full pipeline, automatically selecting the correct downloader
    based on the source URL (YouTube or Spotify).
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"✅ Created temporary directory: {temp_dir}")
            # 1. DOWNLOAD ORIGINAL AUDIO (AUTOMATED SOURCE DETECTION)
            original_audio_path = os.path.join(temp_dir, "original.mp3")
            original_title = ""

            print(f"Detecting source for URL: {source_url}")
            if "youtube.com" in source_url or "youtu.be" in source_url:
                print("-> YouTube source detected. Downloading...")
                original_title = downloader.download_from_youtube(source_url, original_audio_path)
            elif "spotify.com" in source_url:
                print("-> Spotify source detected. Downloading...")
                original_title = downloader.download_from_spotify(source_url, original_audio_path)
            else:
                raise ValueError("Unsupported URL source. Please provide a YouTube or Spotify URL.")
            print(f"✅ Downloaded '{original_title}' to {original_audio_path}")
            
            s3_upload_url = s3_uploader.upload_file_to_s3(original_audio_path, object_name=f"songs/{user_id}/{original_title}.mp3")

            # 2. PROCESS ORIGINAL AUDIO & CREATE SONG RECORD IN DB
            music_desc = extract_analytics.extract_music_analytics(original_audio_path)
            
            song_data_dto = schemas.SongCreateDTO(
                title=original_title,
                owner_id=user_id,
                song_url=s3_upload_url,
                lyrics={},
                description=music_desc
            )
            

            new_song = crud.create_song(db=db, song=song_data_dto)
            print(f"✅ Saved initial song record with ID: {new_song.id}")

            # 3. SPLIT ORIGINAL AUDIO INTO 5 .WAV STEMS
            stems_output_dir = os.path.join(temp_dir, "stems")
            os.makedirs(stems_output_dir) 
            spleeter_wrapper.spleeter_5_stem_split(original_audio_path, stems_output_dir)
            print(f"✅ Split audio into 5 stems in {stems_output_dir}")
            
            # 1. Define the output directory for MP3s
            conv_mp3_dir = os.path.join(os.path.dirname(stems_output_dir), "conv_mp3")
            os.makedirs(conv_mp3_dir, exist_ok=True)

            # 2. List the 5 standard stem filenames
            stem_files = ["vocals.wav", "bass.wav", "drums.wav", "piano.wav", "other.wav"]

            session_id = uuid.uuid4()
            s3_urls = {}

            print("🎵 Converting stems to MP3...")
            
            # 3. Loop through, convert, and save each stem
            for file_name in stem_files:            
                # Construct full input and output paths
                wav_path = os.path.join(stems_output_dir, file_name)
                mp3_path = os.path.join(conv_mp3_dir, file_name.replace(".wav", ".mp3"))
            
                # Check if the source wav file exists before trying to convert
                if os.path.exists(wav_path):
                    # Load the .wav and export as .mp3
                    sound = AudioSegment.from_wav(wav_path)
                    sound.export(mp3_path, format="mp3")
                    print(f"  -> Converted {file_name} to MP3.")
                    s3_object_name = f"stems/{session_id}/{file_name.replace('.wav', '.mp3')}"
                    s3_url = s3_uploader.upload_file_to_s3(mp3_path, object_name=s3_object_name)
                    if s3_url:
                        print(f"  -> Uploaded {file_name} to S3: {s3_url}")
                        s3_urls[file_name.replace('.wav', '')] = s3_url
                    else:
                        print(f"  -> Error uploading {file_name} to S3.")
                
                else:
                    print(f"  -> Warning: {file_name} not found in {stems_output_dir}. Skipping.")
            
            print(f"✅ All stems converted to MP3 in {conv_mp3_dir}")
            
            # Unpack the dictionary into 5 separate variables
            vocal_url = s3_urls.get("vocals")
            bass_url = s3_urls.get("bass")
            drums_url = s3_urls.get("drums")
            piano_url = s3_urls.get("piano")
            other_url = s3_urls.get("other")


            print("Starting parallel audio analysis...")
            all_7_data = parallel_processor.run_analysis_in_parallel(stems_output_dir)
            
            vocal_data = all_7_data.get("vocal")
            bass_data = all_7_data.get("bass")
            drums_data = all_7_data.get("drums")
            piano_data = all_7_data.get("piano")
            other_data = all_7_data.get("other")
            guitar_data = all_7_data.get("guitar")
            violin_data = all_7_data.get("violin")
            flute_data = all_7_data.get("flute")
            
            split_data_dto = schemas.SplitCreateDTO(
                song_id=new_song.id,
                
                bass_audio_url=bass_url,
                bass_description=bass_data,
                
                vocals_audio_url=vocal_url,
                vocals_description=vocal_data,
                
                piano_audio_url=piano_url,
                piano_description=piano_data,
                
                other_audio_url=other_url,
                other_description=other_data,
                
                drum_audio_url=drums_url,
                drum_description=drums_data,
                
                guitar_description=guitar_data,
                violin_description=violin_data,
                flute_description=flute_data
            )
            new_split_record = crud.create_split(db=db, split=split_data_dto)
            print(f"✅ Successfully created database record with ID: {new_split_record.id}")

        print(f"✅ DONE. Temporary directory {temp_dir} and all its contents were automatically deleted. 🗑️")
        return new_song

    except Exception as e:
        print(f"❌ An error occurred during the pipeline: {e}")
        # Optionally roll back any database changes if the process fails midway
        db.rollback()
        return None


