from pathlib import Path
from spleeter.separator import Separator
import uuid

def spleeter_5_stem_split(input_path: str, output_dir: str) -> dict:
    """
    Splits an audio file into 5 stems (vocals, bass, drums, piano, other)
    using Spleeter and returns a dictionary of the output file paths.
    """
    input_path = Path(input_path)
    output_path = Path(output_dir)

    # Load the Spleeter 5stems model directly
    separator = Separator("spleeter:5stems", multiprocess=False)

    # Spleeter will create a subfolder inside the output_dir with the same
    # name as the input file's stem (e.g., 'output/my_song/').
    print(f"Splitting {input_path.name} into 5 stems...")
    separator.separate_to_file(str(input_path), str(output_path))
    print("Splitting complete.")

    # The actual folder where stems are saved
    separation_folder = output_path / input_path.stem

    # Hardcoded list of stems for the 5-stem model
    stem_names = ["vocals", "bass", "drums", "piano", "other"]

    # Return a dictionary mapping stem name to its output file path
    return {
        stem: str(separation_folder / f"{stem}.wav")
        for stem in stem_names
    }
