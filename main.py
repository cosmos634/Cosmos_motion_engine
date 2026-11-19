"""Cosmo Motion Engine command line."""
import argparse
import json
import math
import shutil
import sys
from pathlib import Path

from cosmo_engine import __version__
from cosmo_engine.encoder import encode_frames
from cosmo_engine.renderer import render_frame
from cosmo_engine.validator import ProjectValidationError, validate_project


def load_project(path):
    path = Path(path).resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProjectValidationError(f"invalid JSON: {exc}") from exc
    validate_project(data, path.parent)
    return data, path.parent


def main():
    parser = argparse.ArgumentParser(prog="cosmo", description="Cosmo Motion Engine — Stage 1")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", help="show engine information")
    validate_cmd = sub.add_parser("validate", help="validate a JSON project")
    validate_cmd.add_argument("project")
    render_cmd = sub.add_parser("render", help="render a JSON project to MP4")
    render_cmd.add_argument("project")
    render_cmd.add_argument("--output", default="output/render.mp4")
    args = parser.parse_args()

    try:
        if args.command == "info":
            print(f"Cosmo Motion Engine {__version__} | Stage 1")
            print("Python + Pillow + FFmpeg | JSON projects | sequential rendering")
            return 0
        project, project_dir = load_project(args.project) if args.command in ("validate", "render") else (None, None)
        if args.command == "validate":
            print("Project is valid.")
            return 0
        if args.command == "render":
            if shutil.which("ffmpeg") is None:
                raise RuntimeError("FFmpeg was not found on PATH. Install it first.")
            output = Path(args.output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            frames = math.ceil(project["project"]["duration"] * project["project"]["fps"])
            encode_frames(project, frames, output, render_frame)
            print(f"Rendered {frames} frames: {output}")
            return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
