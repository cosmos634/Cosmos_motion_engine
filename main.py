"""Cosmo Motion Engine command line."""
import argparse
import json
import math
import shutil
import sys
from pathlib import Path

from cosmo_engine import __version__
from cosmo_engine.ai import AIGenerationError, ProjectGenerator
from cosmo_engine.encoder import encode_frames
from cosmo_engine.audio import mux_audio
from cosmo_engine.renderer import render_frame
from cosmo_engine.validator import ProjectValidationError, validate_project


def _resolve_asset(source, project_dir, label):
    resolved = (project_dir / source).resolve()
    if project_dir not in resolved.parents:
        raise ProjectValidationError(f"{label} path escapes project directory")
    if not resolved.is_file():
        raise ProjectValidationError(f"{label} file not found: {source}")
    return str(resolved)


def load_project(path):
    path = Path(path).resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProjectValidationError(f"invalid JSON: {exc}") from exc
    validate_project(data, path.parent)
    for track in data.get("audio", []):
        track["source"] = _resolve_asset(track["source"], path.parent, "audio source")
    for scene in data["scenes"]:
        for element in scene["elements"]:
            if element.get("font"):
                element["font"] = _resolve_asset(element["font"], path.parent, "font")
            if element.get("type") in {"image", "video"}:
                element["source"] = _resolve_asset(element["source"], path.parent, "media source")
    return data, path.parent


def main():
    parser = argparse.ArgumentParser(
        prog="cosmo", description="Cosmo Motion Engine — Stage 6"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", help="show engine information")

    validate_cmd = sub.add_parser("validate", help="validate a JSON project")
    validate_cmd.add_argument("project")

    render_cmd = sub.add_parser("render", help="render a JSON project to MP4")
    render_cmd.add_argument("project")
    render_cmd.add_argument("--output", default="output/render.mp4")

    generate_cmd = sub.add_parser("generate", help="generate a project JSON from a text prompt")
    generate_cmd.add_argument("--prompt", required=True)
    generate_cmd.add_argument("--output", default="projects/generated/project.json")
    generate_cmd.add_argument("--provider", choices=("auto", "gemini", "groq"), default="auto")
    generate_cmd.add_argument("--width", type=int, default=1080)
    generate_cmd.add_argument("--height", type=int, default=1920)
    generate_cmd.add_argument("--fps", type=int, default=30)
    generate_cmd.add_argument("--duration", type=float, default=20)

    args = parser.parse_args()

    try:
        if args.command == "info":
            print(f"Cosmo Motion Engine {__version__} | Stage 6")
            print("Python + Pillow + FFmpeg | JSON projects | Gemini + Groq")
            return 0

        if args.command == "generate":
            project, provider = ProjectGenerator().generate(
                args.prompt,
                provider=args.provider,
                width=args.width,
                height=args.height,
                fps=args.fps,
                duration=args.duration,
            )
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(project, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"Generated and validated with {provider}: {output}")
            print("Next: python main.py render " + str(output))
            return 0

        project, project_dir = load_project(args.project)
        if args.command == "validate":
            print("Project is valid.")
            return 0

        if args.command == "render":
            if shutil.which("ffmpeg") is None:
                raise RuntimeError("FFmpeg was not found on PATH. Install it first.")
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            frames = math.ceil(project["project"]["duration"] * project["project"]["fps"])
            tracks = project.get("audio", [])
            if tracks:
                temp_video = output.with_name(output.stem + ".video_tmp.mp4")
                try:
                    encode_frames(project, frames, temp_video, render_frame)
                    mux_audio(temp_video, tracks, output, project["project"]["duration"])
                finally:
                    if temp_video.exists():
                        temp_video.unlink()
                print(f"Rendered {frames} frames with {len(tracks)} audio track(s): {output}")
            else:
                encode_frames(project, frames, output, render_frame)
                print(f"Rendered {frames} frames: {output}")
            return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
