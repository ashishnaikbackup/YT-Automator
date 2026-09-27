import asyncio
from pathlib import Path
import edge_tts

from config import VOICE


async def _generate(text: str, output: Path):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(output))


def generate_voice(text: str, output: Path):
    asyncio.run(_generate(text, output))
    return output
