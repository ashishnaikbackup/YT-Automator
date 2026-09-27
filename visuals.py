from __future__ import annotations

import re
from pathlib import Path


def split_scenes(narration: str, max_scenes: int = 6) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", narration.strip()) if s.strip()]
    if not sentences:
        return []
    chunk_size = max(1, (len(sentences) + max_scenes - 1) // max_scenes)
    return [" ".join(sentences[i:i + chunk_size]) for i in range(0, len(sentences), chunk_size)][:max_scenes]


def build_visual_plan(narration: str, output_path: Path) -> list[dict]:
    scenes = split_scenes(narration)
    plan = []
    for index, scene in enumerate(scenes, 1):
        words = scene.split()
        keyword = " ".join(words[:8])
        plan.append({
            "scene": index,
            "narration": scene,
            "visual_query": keyword,
            "asset_strategy": "free_or_generated_asset",
        })

    lines = ["# Visual plan", ""]
    for item in plan:
        lines.append(f"Scene {item['scene']}: {item['visual_query']}")
        lines.append(f"Narration: {item['narration']}")
        lines.append(f"Asset strategy: {item['asset_strategy']}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return plan
