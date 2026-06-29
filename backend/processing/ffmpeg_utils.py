import subprocess
import json
import os
import shutil

# Use the static ffmpeg binary from imageio_ffmpeg if system ffmpeg not available
def _get_ffmpeg():
    if shutil.which("ffmpeg"):
        return "ffmpeg", "ffprobe"
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        # ffprobe is in the same dir for static builds
        probe = os.path.join(os.path.dirname(exe), "ffprobe-linux-x86_64-v7.0.2")
        if not os.path.exists(probe):
            probe = exe  # fallback
        return exe, probe
    except Exception:
        return "ffmpeg", "ffprobe"

FFMPEG_BIN, FFPROBE_BIN = _get_ffmpeg()


def run_ffmpeg(*args):
    cmd = [FFMPEG_BIN, "-y"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr[-800:]}")
    return result


def get_video_info(path: str) -> dict:
    cmd = [FFPROBE_BIN, "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Try ffmpeg as ffprobe fallback
        cmd2 = [FFMPEG_BIN, "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", path]
        result = subprocess.run(cmd2, capture_output=True, text=True)
    return json.loads(result.stdout)


def get_video_duration(path: str) -> float:
    data = get_video_info(path)
    return float(data["format"]["duration"])


def get_video_dimensions(path: str) -> tuple:
    data = get_video_info(path)
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            return stream["width"], stream["height"]
    return 1920, 1080


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
