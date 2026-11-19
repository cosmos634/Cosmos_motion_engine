"""Automatic Russian narration and original procedural audio assets."""
import asyncio
import math
import os
import random
import struct
import subprocess
import wave
from pathlib import Path

SAMPLE_RATE = 22050


def _write_tone_bed(path, duration):
    total = max(1, int(SAMPLE_RATE * duration))
    chunk_size = 4096
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        for offset in range(0, total, chunk_size):
            count = min(chunk_size, total - offset)
            samples = bytearray()
            for index in range(offset, offset + count):
                t = index / SAMPLE_RATE
                fade = min(1.0, t / 1.8, max(0.0, (duration - t) / 2.5))
                pulse = 0.72 + 0.18 * math.sin(2 * math.pi * 0.11 * t)
                signal = (0.48 * math.sin(2 * math.pi * 110.0 * t)
                          + 0.25 * math.sin(2 * math.pi * 164.81 * t)
                          + 0.13 * math.sin(2 * math.pi * 220.0 * t))
                value = int(max(-1.0, min(1.0, signal * pulse * fade * 0.10)) * 32767)
                samples.extend(struct.pack("<h", value))
            output.writeframesraw(samples)


def _write_whoosh(path, duration=0.75, seed=17):
    rng = random.Random(seed)
    total = int(SAMPLE_RATE * duration)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        chunk_size = 4096
        for offset in range(0, total, chunk_size):
            count = min(chunk_size, total - offset)
            samples = bytearray()
            for index in range(offset, offset + count):
                t = index / SAMPLE_RATE
                progress = t / duration
                envelope = math.sin(math.pi * progress) ** 1.7
                noise = rng.uniform(-1.0, 1.0)
                sweep = math.sin(2 * math.pi * (180 + 700 * progress) * t)
                value = int((noise * 0.65 + sweep * 0.35) * envelope * 0.11 * 32767)
                samples.extend(struct.pack("<h", value))
            output.writeframesraw(samples)


async def _synthesize_edge_tts(text, destination):
    import edge_tts
    voice = os.getenv("COSMO_TTS_VOICE", "ru-RU-DmitryNeural")
    communicate = edge_tts.Communicate(text, voice, rate="+0%", volume="+0%")
    await communicate.save(str(destination))


def _validate_mp3(path):
    """Reject empty, truncated, or non-audio TTS responses using FFprobe."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size < 1024:
        raise RuntimeError("TTS returned an empty or suspiciously small MP3 file")
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 or "mp3" not in (result.stdout or "").lower():
        detail = (result.stderr or result.stdout or "no MP3 audio stream detected").strip()
        raise RuntimeError(f"TTS output is not a valid MP3: {detail[-500:]}")


def create_audio_tracks(project, project_dir):
    """Create narration/music/SFX assets and return schema-compatible tracks."""
    settings = project["project"]
    duration = float(settings["duration"])
    project_dir = Path(project_dir).resolve()
    audio_dir = project_dir / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    tracks = []
    warnings = []

    music_path = audio_dir / "ambient_music.wav"
    _write_tone_bed(music_path, duration)
    tracks.append({
        "kind": "music", "source": str(music_path.relative_to(project_dir)),
        "start": 0, "duration": duration, "volume": 0.75,
        "fade_in": min(2.0, duration / 4), "fade_out": min(2.5, duration / 3),
        "loop": False,
    })

    whoosh_path = audio_dir / "scene_whoosh.wav"
    _write_whoosh(whoosh_path)
    for index, scene in enumerate(project.get("scenes", [])):
        start = float(scene.get("start", 0))
        if index == 0 or start >= duration:
            continue
        effect_duration = min(0.75, duration - start)
        if effect_duration < 0.001:
            continue
        tracks.append({
            "kind": "sfx", "source": str(whoosh_path.relative_to(project_dir)),
            "start": start, "duration": effect_duration, "volume": 0.65,
            "fade_in": 0.04, "fade_out": min(0.25, effect_duration / 2),
            "loop": False,
        })

    narration = project.get("voiceover", "").strip()
    if narration:
        voice_path = audio_dir / "narration_ru.mp3"
        temp_voice_path = audio_dir / "narration_ru.tmp.mp3"
        for stale_path in (voice_path, temp_voice_path):
            if stale_path.exists():
                stale_path.unlink()
        try:
            asyncio.run(_synthesize_edge_tts(narration, temp_voice_path))
            _validate_mp3(temp_voice_path)
            temp_voice_path.replace(voice_path)
            tracks.append({
                "kind": "narration", "source": str(voice_path.relative_to(project_dir)),
                "start": 0, "duration": duration, "volume": 1.0,
                "fade_in": 0.05, "fade_out": 0.15, "loop": False,
            })
        except Exception as exc:
            if temp_voice_path.exists():
                temp_voice_path.unlink()
            if voice_path.exists():
                voice_path.unlink()
            warnings.append(f"Russian TTS unavailable: {type(exc).__name__}: {exc}")
    else:
        warnings.append("No Russian voiceover text was supplied; narration was skipped")
    return tracks, warnings
