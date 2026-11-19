"""FFmpeg raw RGB encoder. Frames are streamed, never accumulated."""
import subprocess


def encode_frames(project, frame_count, output_path, frame_renderer):
    p = project["project"]
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{p['width']}x{p['height']}", "-r", str(p["fps"]),
        "-i", "-", "-an", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        assert process.stdin is not None
        for index in range(frame_count):
            frame = frame_renderer(project, index)
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        return_code = process.wait()
    except Exception:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
        process.kill()
        process.wait()
        raise
    if return_code != 0:
        raise RuntimeError(f"FFmpeg exited with status {return_code}")
