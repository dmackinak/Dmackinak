import re
from typing import List, Dict

# Keywords that signal high-engagement YouTube moments
HOOK_KEYWORDS = [
    "secret", "tip", "trick", "hack", "you won't believe", "amazing", "incredible",
    "wait", "actually", "truth", "mistake", "never", "always", "best", "worst",
    "how to", "why", "what if", "did you know", "this is why", "here's why",
    "warning", "stop", "don't", "must", "need to", "game changer", "viral",
    "controversial", "unpopular opinion", "hot take", "real talk", "honest",
    "finally", "revealed", "exposed", "proof", "wrong", "right", "important",
    "huge", "massive", "insane", "crazy", "wild", "unbelievable", "shocking",
    "breaking", "exclusive", "first", "only", "free", "easy", "simple", "quick",
]


def score_segment(text: str) -> float:
    text_lower = text.lower()
    score = 0.0

    if "?" in text:
        score += 2.5  # Questions are engaging hooks
    if "!" in text:
        score += 1.5  # Exclamations show energy

    for kw in HOOK_KEYWORDS:
        if kw in text_lower:
            score += 1.5
            break  # Count once per segment to avoid spam

    words = text.split()
    word_count = len(words)
    if 6 <= word_count <= 30:
        score += 1.0  # Good digestible length
    elif word_count < 3:
        score -= 1.5  # Too short

    if re.search(r"\b\d+\b", text):
        score += 0.5  # Numbers = tips/stats

    # Penalise filler
    filler = ["um", "uh", "like", "you know", "basically", "literally"]
    filler_count = sum(1 for f in filler if f in text_lower)
    score -= filler_count * 0.3

    return max(score, 0.0)


def find_best_clips(
    segments: List[Dict],
    total_duration: float,
    min_duration: float = 20,
    max_duration: float = 55,
    max_clips: int = 5,
) -> List[Dict]:
    if not segments:
        return _fallback_clips(total_duration, min_duration, max_duration, max_clips)

    for seg in segments:
        seg["score"] = score_segment(seg["text"])

    # Build windows starting at each segment
    windows = []
    for i, seg in enumerate(segments):
        win_start = seg["start"]
        win_end = seg["end"]
        win_score = seg["score"]
        texts = [seg["text"]]
        top_text = seg["text"]
        top_score = seg["score"]

        for j in range(i + 1, len(segments)):
            ns = segments[j]
            if ns["end"] - win_start > max_duration:
                break
            win_end = ns["end"]
            win_score += ns["score"]
            texts.append(ns["text"])
            if ns["score"] > top_score:
                top_score = ns["score"]
                top_text = ns["text"]

        dur = win_end - win_start
        if min_duration <= dur <= max_duration:
            windows.append({
                "start": round(win_start, 2),
                "end": round(win_end, 2),
                "score": round(win_score, 2),
                "transcript": " ".join(texts),
                "highlight": top_text[:120],
            })

    if not windows:
        return _fallback_clips(total_duration, min_duration, max_duration, max_clips)

    windows.sort(key=lambda w: w["score"], reverse=True)

    selected: List[Dict] = []
    for window in windows:
        if _overlaps(window, selected, threshold=8):
            continue
        selected.append(window)
        if len(selected) >= max_clips:
            break

    selected.sort(key=lambda w: w["start"])
    return selected


def _overlaps(candidate: Dict, selected: List[Dict], threshold: float = 8) -> bool:
    for sel in selected:
        overlap = min(candidate["end"], sel["end"]) - max(candidate["start"], sel["start"])
        if overlap > threshold:
            return True
    return False


def _fallback_clips(
    total_duration: float,
    min_duration: float,
    max_duration: float,
    max_clips: int,
) -> List[Dict]:
    """Even distribution when no transcript is available."""
    target = (min_duration + max_duration) / 2
    # Skip first 10% (intro) and last 5% (outro)
    eff_start = total_duration * 0.10
    eff_end = total_duration * 0.95
    eff_dur = eff_end - eff_start

    clips = []
    n = min(max_clips, max(1, int(eff_dur / target)))
    step = eff_dur / n

    for i in range(n):
        start = eff_start + step * i
        end = min(start + target, eff_end)
        if end - start < min_duration:
            continue
        clips.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "score": 0.0,
            "transcript": "",
            "highlight": f"Segment {i + 1}",
        })

    return clips
