import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cosmo_engine.audio_generation import create_audio_tracks
from cosmo_engine.validator import validate_project


def project():
    return {
        "version": 1,
        "project": {
            "width": 320, "height": 180, "fps": 12,
            "duration": 4, "background": "#101426",
        },
        "voiceover": "Сегодня мы отправимся в космос.",
        "scenes": [
            {"id": "one", "start": 0, "duration": 2, "elements": []},
            {"id": "two", "start": 2, "duration": 2, "elements": []},
        ],
    }


class AudioGenerationTests(unittest.TestCase):
    def test_creates_music_and_scene_effects_when_tts_fails(self):
        data = project()
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "cosmo_engine.audio_generation._synthesize_edge_tts",
                side_effect=RuntimeError("offline"),
            ):
                tracks, warnings = create_audio_tracks(data, directory)
            self.assertEqual([item["kind"] for item in tracks], ["music", "sfx"])
            self.assertEqual(warnings, ["Russian TTS unavailable: RuntimeError: offline"])
            self.assertEqual(tracks[0]["volume"], 0.75)
            self.assertEqual(tracks[1]["volume"], 0.65)
            for track in tracks:
                self.assertTrue((Path(directory) / track["source"]).is_file())
            data["audio"] = tracks
            validate_project(data, directory)

    def test_adds_russian_narration_after_mp3_validation(self):
        async def fake_tts(text, destination):
            Path(destination).write_bytes(b"test-audio-payload")

        data = project()
        with tempfile.TemporaryDirectory() as directory:
            with patch("cosmo_engine.audio_generation._validate_mp3") as validate:
                with patch("cosmo_engine.audio_generation._synthesize_edge_tts", fake_tts):
                    tracks, warnings = create_audio_tracks(data, directory)
            self.assertEqual(warnings, [])
            self.assertEqual([item["kind"] for item in tracks], ["music", "sfx", "narration"])
            self.assertTrue(validate.called)
            narration_path = Path(directory) / tracks[-1]["source"]
            self.assertTrue(narration_path.is_file())
            self.assertFalse((Path(directory) / "assets/audio/narration_ru.tmp.mp3").exists())
            data["audio"] = tracks
            validate_project(data, directory)

    def test_rejects_empty_tts_output_without_adding_narration(self):
        async def empty_tts(text, destination):
            Path(destination).write_bytes(b"")

        data = project()
        with tempfile.TemporaryDirectory() as directory:
            with patch("cosmo_engine.audio_generation._synthesize_edge_tts", empty_tts):
                tracks, warnings = create_audio_tracks(data, directory)
            self.assertEqual([item["kind"] for item in tracks], ["music", "sfx"])
            self.assertTrue(any("empty or suspiciously small" in item for item in warnings))
            self.assertFalse((Path(directory) / "assets/audio/narration_ru.mp3").exists())


if __name__ == "__main__":
    unittest.main()
