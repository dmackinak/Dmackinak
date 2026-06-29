import subprocess
import json
import os
import shutil

# Locate the ffmpeg binary (imageio_ffmpeg ships a static build)
def _get_ffmpeg() -> str:
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG_BIN = _get_ffmpeg()


def run_ffmpeg(*args):
    cmd = [FFMPEG_BIN, "-y"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr[-800:]}")
    return result


def _probe_with_av(path: str) -> dict:
    """Use PyAV to read container metadata — no ffprobe binary needed."""
    import av
    with av.open(path) as container:
        duration = float(container.duration) / 1_000_000  # microseconds → seconds
        width, height = 1920, 1080
        for stream in container.streams:
            if stream.type == "video":
                width = stream.width
                height = stream.height
                break
        return {"duration": duration, "width": width, "height": height}


def get_video_duration(path: str) -> float:
    return _probe_with_av(path)["duration"]


def get_video_dimensions(path: str) -> tuple:
    info = _probe_with_av(path)
    return info["width"], info["height"]


def extract_clip(input_path: str, output_path: str, start: float, end: float):
    duration = end - start
    run_ffmpeg(
        "-ss", str(round(start, 3)),
        "-i", input_path,
        "-t", str(round(duration, 3)),
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    )


def crop_to_vertical(input_path: str, output_path: str):
    """Crop video to 9:16 aspect ratio for YouTube Shorts."""
    w, h = get_video_dimensions(input_path)
    target_w = int(h * 9 / 16)

    if target_w > w:
        # Video already narrower — letterbox pad to 9:16
        target_h = int(w * 16 / 9)
        vf = f"pad={w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black,scale=1080:1920:flags=lanczos"
    else:
        # Center-crop width to 9:16
        x_offset = (w - target_w) // 2
        vf = f"crop={target_w}:{h}:{x_offset}:0,scale=1080:1920:flags=lanczos"

    run_ffmpeg(
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    )


def add_watermark(
    input_path: str,
    output_path: str,
    channel_name: str,
    position: str = "bottom-right",
    color: str = "#FFFFFF",
    fontsize: int = 28,
):
    """Burn channel name text onto video."""
    if not channel_name.strip():
        shutil.copy(input_path, output_path)
        return

    ffmpeg_color = color.lstrip("#")
    margin = 24

    pos_map = {
        "top-left":      f"x={margin}:y={margin}",
        "top-right":     f"x=w-tw-{margin}:y={margin}",
        "bottom-left":   f"x={margin}:y=h-th-{margin}",
        "bottom-right":  f"x=w-tw-{margin}:y=h-th-{margin}",
        "top-center":    f"x=(w-tw)/2:y={margin}",
        "bottom-center": f"x=(w-tw)/2:y=h-th-{margin}",
    }
    pos = pos_map.get(position, pos_map["bottom-right"])

    # Escape chars that break FFmpeg drawtext
    safe_name = (
        channel_name
        .replace("\\", "\\\\")
        .replace("'", "’")
        .replace(":", "\\:")
    )

    drawtext = (
        f"drawtext=text='{safe_name}'"
        f":fontsize={fontsize}"
        f":fontcolor=0x{ffmpeg_color}"
        f":box=1:boxcolor=black@0.45:boxborderw=10"
        f":{pos}"
    )

    run_ffmpeg(
        "-i", input_path,
        "-vf", drawtext,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    )
