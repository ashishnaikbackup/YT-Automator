from pathlib import Path
import re

p = Path('pipeline.py')
s = p.read_text(encoding='utf-8')

# More visual changes: 12 images instead of 8.
s = s.replace('def download_visuals(topic: str, script: str, job_dir: Path, count: int = 8):',
              'def download_visuals(topic: str, script: str, job_dir: Path, count: int = 12):')

# Replace the image-only renderer with a faster Shorts-style cut every ~1.5-3 seconds.
start = s.index('def make_visual_video(images, out_path: Path, duration: float):')
end = s.index('\n\ndef make_ass(', start)
new_func = '''def make_visual_video(images, out_path: Path, duration: float):
    ffmpeg = ffmpeg_path()
    clip_dir = out_path.parent / "clips"
    clip_dir.mkdir(exist_ok=True)

    # Fast pacing: change visuals frequently instead of holding one photo for most of the Short.
    # Cap each shot at 2.6s; for short videos this naturally uses fewer shots.
    shot_count = min(len(images), max(1, int(duration / 2.0 + 0.5)))
    selected = images[:shot_count]
    each = duration / len(selected)
    clips = []

    for i, image in enumerate(selected):
        clip = clip_dir / f"clip_{i+1}.mp4"
        # Alternate zoom direction to make still images feel more dynamic.
        if i % 2 == 0:
            zoom = "min(zoom+0.0018,1.16)"
            x = "iw/2-(iw/zoom/2)"
            y = "ih/2-(ih/zoom/2)"
        else:
            zoom = "max(1.16-0.0018*(on),1.0)"
            x = "iw/2-(iw/zoom/2)"
            y = "ih/2-(ih/zoom/2)"
        vf = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"zoompan=z='{zoom}':x='{x}':y='{y}':d=1:s=1080x1920:fps=30,format=yuv420p"
        )
        subprocess.run([
            ffmpeg, "-y", "-loop", "1", "-i", str(image["path"]),
            "-t", f"{each:.3f}", "-vf", vf, "-an", "-c:v", "libx264",
            "-preset", "veryfast", "-pix_fmt", "yuv420p", str(clip)
        ], check=True)
        clips.append(clip)

    concat = clip_dir / "concat.txt"
    concat.write_text(
        "\\n".join(f"file '{p.resolve().as_posix()}'" for p in clips),
        encoding="utf-8"
    )
    subprocess.run([
        ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c", "copy", "-t", f"{duration:.3f}", str(out_path)
    ], check=True)
'''
s = s[:start] + new_func + s[end:]
p.write_text(s, encoding='utf-8')
print('Fast-paced visual editing upgrade applied.')
print('Visuals: up to 12 images; cuts roughly every 2 seconds; stronger motion.')
