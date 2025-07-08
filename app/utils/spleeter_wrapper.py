from pathlib import Path
from spleeter.separator import Separator
import uuid

def spleeter_split(input_path: str, output_dir: str = "output", stem_type: str = "5stems") -> dict:
    if stem_type not in ["2stems", "4stems", "5stems"]:
        raise ValueError("stem_type must be '2stems', '4stems', or '5stems'.")

    input_path = Path(input_path)
    base_name = input_path.stem
    unique_id = str(uuid.uuid4())

    # Output will be: output/base_name/uuid/
    result_dir = Path(output_dir) / f"{base_name}" / unique_id
    result_dir.mkdir(parents=True, exist_ok=True)

    # Load Spleeter model
    if stem_type in ["2stems", "4stems"]:
        separator = Separator(f"spleeter:{stem_type}", multiprocess=False)
    else:
        model_config = Path("pretrained_models") / stem_type / "config.json"
        print(f"Loading custom config: {model_config}")
        separator = Separator(params_descriptor=str(model_config), multiprocess=False)

    # Spleeter will create one subfolder inside result_dir with the same name as the input file
    separator.separate_to_file(str(input_path), str(result_dir))

    # Get the actual separation folder name created by spleeter
    separation_folder = result_dir / base_name  # e.g., .../uuid/filename_without_ext/

    stems = {
        "2stems": ["vocals", "accompaniment"],
        "4stems": ["vocals", "bass", "drums", "other"],
        "5stems": ["vocals", "bass", "drums", "piano", "other"],
    }[stem_type]

    return {
        stem: str(separation_folder / f"{stem}.wav")
        for stem in stems
    }
