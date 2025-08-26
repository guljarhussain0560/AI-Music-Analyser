# parallel_processor.py

import os
import multiprocessing
import time
from app.utils import extract_analytics

def run_analysis_in_parallel(stems_output_dir):
    initialTime = time.time()
    """
    Analyzes all audio stems in parallel and returns a dictionary of the results.
    """
    tasks = [
        ("vocal", extract_analytics.extract_vocal_analytics, "vocals.wav"),
        ("bass", extract_analytics.extract_bass_analytics, "bass.wav"),
        ("drums", extract_analytics.extract_drums_analytics, "drums.wav"),
        ("piano", extract_analytics.extract_piano_analytics, "piano.wav"),
        ("other", extract_analytics.extract_other_analytics, "other.wav"),
        ("guitar", extract_analytics.extract_guitar_analytics, "other.wav"),
        ("violin", extract_analytics.extract_violin_analytics, "other.wav"),
        ("flute", extract_analytics.extract_flute_analytics, "other.wav"),
    ]

    with multiprocessing.Pool() as pool:
        async_results = [
            pool.apply_async(func, args=(os.path.join(stems_output_dir, filename),))
            for _, func, filename in tasks
        ]
        results_list = [res.get() for res in async_results]

    # Map the results back to a dictionary for easy access
    all_descriptions = {task[0]: result for task, result in zip(tasks, results_list)}
    print(f"✅ All analyses complete in {time.time() - initialTime:.2f} seconds.")
    return all_descriptions