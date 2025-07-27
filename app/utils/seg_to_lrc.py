def convert_lyrics_to_lrc(segments: list[dict]) -> str:
    """
    Convert a list of lyric segments to LRC format string.
    If the lyric text is empty, include the timestamp with empty content.

    Args:
        segments (list): A list of dicts with 'start', 'end', 'text'.

    Returns:
        str: LRC-formatted string.
    """
    def format_timestamp(seconds):
        minutes = int(seconds // 60)
        sec = seconds % 60
        return f"[{minutes:02d}:{sec:05.2f}]"

    lrc_lines = []

    for item in segments:
        start = item.get("start")
        if start is None:
            continue  # skip if no timestamp

        text = item.get("text", "")
        text = text.strip().replace('"', '').replace('\n', ' ')

        timestamp = format_timestamp(start)
        lrc_lines.append(f"{timestamp}{text}")  # even if text is empty

    lrc_lines.sort()
    return "\n".join(lrc_lines)
