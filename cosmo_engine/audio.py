"""Memory-conscious FFmpeg audio muxing for Stage 3."""
import subprocess


def build_audio_command(video_path, tracks, output_path, project_duration):
    """Build a fixed-argument FFmpeg command; track data is never shell-executed."""
    command = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path)]
    for track in tracks:
        if track.get("loop", False):
            command.extend(["-stream_loop", "-1"])
        command.extend(["-i", str(track["source"])])

    filters = []
    labels = []
    for index, track in enumerate(tracks, start=1):
        label = f"a{index - 1}"
        duration = float(track["duration"])
        chain = [
            f"[{index}:a]atrim=duration={duration:.6f}",
            "asetpts=PTS-STARTPTS",
            f"volume={float(track['volume']):.6f}",
        ]
        fade_in = float(track.get("fade_in", 0))
        fade_out = float(track.get("fade_out", 0))
        if fade_in > 0:
            chain.append(f"afade=t=in:st=0:d={fade_in:.6f}")
        if fade_out > 0:
            chain.append(
                f"afade=t=out:st={duration - fade_out:.6f}:d={fade_out:.6f}"
            )
        delay_ms = round(float(track["start"]) * 1000)
        chain.append(f"adelay=delays={delay_ms}:all=1")
        filters.append(",".join(chain) + f"[{label}]")
        labels.append(f"[{label}]")

    filters.append(
        "".join(labels)
        + f"amix=inputs={len(tracks)}:duration=longest:dropout_transition=0,"
        + "alimiter=limit=0.95[aout]"
    )
    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", "0:v:0", "-map", "[aout]",
        "-t", f"{float(project_duration):.6f}",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(output_path),
    ])
    return command


def mux_audio(video_path, tracks, output_path, project_duration):
    if not tracks:
        raise ValueError("mux_audio requires at least one audio track")
    command = build_audio_command(video_path, tracks, output_path, project_duration)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or "unknown FFmpeg error").strip()
        raise RuntimeError(f"Audio mux failed: {detail[-1200:]}")
    return output_path
