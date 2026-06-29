from typing import List, Dict


def transcribe_video(video_path: str) -> List[Dict]:
    """
    Transcribe video using faster-whisper (local, no API key needed).
    Returns list of {start, end, text} segments.
    """
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(
            video_path,
            beam_size=5,
            vad_filter=True,
            word_timestamps=False,
        )
        return [
            {"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip()}
            for seg in segments
            if seg.text.strip()
        ]
    except Exception as e:
        print(f"[transcriber] faster-whisper failed: {e}")
        return []
