from datetime import datetime
from pathlib import Path

from config import OUTPUTS
from script_generator import build_script_prompt, save_script
from voice import generate_voice
from captions import create_srt
from renderer import render_short


def main():
    print("YT-Automator — V1 Prompt to Short")
    topic = input("Enter your video topic: ").strip()
    if not topic:
        raise SystemExit("A topic is required.")

    duration = input("Target duration in seconds [45]: ").strip() or "45"
    duration = int(duration)

    job_dir = OUTPUTS / datetime.now().strftime("%Y%m%d_%H%M%S")
    job_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_script_prompt(topic, duration)
    (job_dir / "script_prompt.txt").write_text(prompt + "\n", encoding="utf-8")

    print("\nPrompt created. Paste this into your chosen AI model:")
    print("\n" + prompt + "\n")

    narration = input("Paste the generated narration here (or press Enter to stop): ").strip()
    if not narration:
        print(f"Saved prompt to: {job_dir / 'script_prompt.txt'}")
        return

    script_path = job_dir / "script.txt"
    save_script(narration, script_path)

    audio_path = job_dir / "voice.mp3"
    generate_voice(narration, audio_path)

    from moviepy import AudioFileClip
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration
    audio.close()

    srt_path = job_dir / "captions.srt"
    create_srt(narration, duration, srt_path)

    video_path = job_dir / "final_short.mp4"
    render_short(narration, audio_path, video_path)

    print("\nDone!")
    print(f"Script:   {script_path}")
    print(f"Voice:    {audio_path}")
    print(f"Captions: {srt_path}")
    print(f"Video:    {video_path}")


if __name__ == "__main__":
    main()
