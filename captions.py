import re
from pathlib import Path


def _timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    whole = int(secs)
    millis = int(round((secs - whole) * 1000))
    if millis == 1000:
        whole += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{whole:02d},{millis:03d}"


def create_srt(narration: str, duration: float, output_path: Path, words_per_caption: int = 6):
    words = re.findall(r"\S+", narration)
    if not words:
        output_path.write_text("", encoding="utf-8")
        return output_path

    chunks = [words[i:i + words_per_caption] for i in range(0, len(words), words_per_caption)]
    step = duration / len(chunks)
    lines = []

    for index, chunk in enumerate(chunks, start=1):
        start = (index - 1) * step
        end = min(index * step, duration)
        lines.append(f"{index}\n{_timestamp(start)} --> {_timestamp(end)}\n{' '.join(chunk)}\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
