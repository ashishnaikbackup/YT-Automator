import textwrap


def build_script_prompt(topic: str, duration_seconds: int = 45) -> str:
    return textwrap.dedent(f"""
    Write a YouTube Short script about: {topic}

    Requirements:
    - Target duration: {duration_seconds} seconds.
    - Start with a strong hook in the first sentence.
    - Use simple spoken English.
    - Keep the pacing fast and natural.
    - Give useful, factual information.
    - Do not invent statistics, quotes, or events.
    - End with a short call to action.
    - Return only the narration, with no headings or stage directions.
    """).strip()


def save_script(text: str, path):
    path.write_text(text.strip() + "\n", encoding="utf-8")
