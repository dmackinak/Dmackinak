import os
import asyncio
from typing import Callable, List, Dict, Optional

from .transcriber import transcribe_video
from .analyzer import find_best_clips
from .ffmpeg_utils import (
    get_video_duration,
    extract_clip,
    crop_to_vertical,
    add_watermark,
)


def process_video(
    video_path: str,
    clips_dir: str,
    settings: dict,
    update_progress: Optional[Callable[[int, str], None]] = None,
) -> List[Dict]:

    def prog(pct: int, msg: str):
        if update_progress:
            update_progress(pct, msg)

    prog(5, "Reading video...")
    duration = get_video_duration(video_path)

    prog(10, "Transcribing audio — this takes a minute on first run...")
    segments = transcribe_video(video_path)
    transcript_found = len(segments) > 0

    prog(50, "Scoring moments...")
    clips_info = find_best_clips(
        segments,
        duration,
        min_duration=settings.get("short_duration_min", 20),
        max_duration=settings.get("short_duration_max", 55),
        max_clips=settings.get("max_clips", 5),
    )

    prog(58, f"Cutting {len(clips_info)} clips...")
    results = []

    for i, clip in enumerate(clips_info):
        base_pct = 58 + int((i / max(len(clips_info), 1)) * 38)
        prog(base_pct, f"Processing clip {i + 1}/{len(clips_info)}...")

        raw = os.path.join(clips_dir, f"_raw_{i}.mp4")
        vert = os.path.join(clips_dir, f"_vert_{i}.mp4")
        final = os.path.join(clips_dir, f"short_{i + 1}.mp4")

        extract_clip(video_path, raw, clip["start"], clip["end"])
        crop_to_vertical(raw, vert)
        add_watermark(
            vert,
            final,
            channel_name=settings.get("channel_name", ""),
            position=settings.get("watermark_position", "bottom-right"),
            color=settings.get("watermark_color", "#FFFFFF"),
            fontsize=int(settings.get("watermark_size", 28)),
        )

        for tmp in (raw, vert):
            if os.path.exists(tmp):
                os.remove(tmp)

        results.append({
            "id": f"short_{i + 1}.mp4",
            "filename": f"short_{i + 1}.mp4",
            "start": clip["start"],
            "end": clip["end"],
            "duration": round(clip["end"] - clip["start"], 1),
            "score": clip["score"],
            "highlight": clip.get("highlight", ""),
            "transcript": clip.get("transcript", ""),
            "has_transcript": transcript_found,
        })

    return results
