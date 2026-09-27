import textwrap


def build_script_prompt(topic: str, duration_seconds: int = 45, research: list[dict] | None = None) -> str:
    sources = ""
    if research:
        source_lines = []
        for item in research:
            source_lines.append(f"- {item.get('title', '')} | {item.get('source', '')} | {item.get('url', '')}")
        sources = "\n\nRecent research sources:\n" + "\n".join(source_lines)

    return textwrap.dedent(f"""
    Write a YouTube Short script about: {topic}

    Requirements:
    - Target duration: {duration_seconds} seconds.
    - Start with a strong hook in the first sentence.
    - Use simple spoken English.
    - Keep the pacing fast and natural.
    - Give useful, factual information.
    - Use the research sources below when relevant.
    - Do not invent statistics, quotes, or events.
    - If the sources disagree or do not support a claim, leave the claim out.
    - End with a short call to action.
    - Return only the narration, with no headings or stage directions.
    {sources}
    """).strip()


def save_script(text: str, path):
    path.write_text(text.strip() + "\n", encoding="utf-8")
