from pathlib import Path

from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, TextClip

from config import VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH


def render_short(narration: str, audio_path: Path, output_path: Path):
    """Render a simple 1080x1920 Short with animated-style readable text.

    This intentionally uses a generated background rather than copyrighted stock footage.
    Later versions can insert researched/generated visual assets per scene.
    """
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    background = ColorClip(
        size=(VIDEO_WIDTH, VIDEO_HEIGHT),
        color=(18, 18, 24),
        duration=duration,
    )

    text = TextClip(
        text=narration,
        font_size=64,
        color="white",
        method="caption",
        size=(VIDEO_WIDTH - 140, VIDEO_HEIGHT - 260),
        text_align="center",
        horizontal_align="center",
        vertical_align="center",
    ).with_duration(duration).with_position("center")

    video = CompositeVideoClip([background, text], size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    video = video.with_audio(audio)
    video.write_videofile(
        str(output_path),
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
    )

    audio.close()
    video.close()
    return output_path
