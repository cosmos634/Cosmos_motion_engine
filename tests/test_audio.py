import unittest

from cosmo_engine.audio import build_audio_command


class AudioCommandTests(unittest.TestCase):
    def setUp(self):
        self.track = {
            "kind": "narration", "source": "/tmp/voice.wav",
            "start": 1.25, "duration": 3, "volume": 0.8,
            "fade_in": 0.2, "fade_out": 0.4, "loop": False,
        }

    def test_builds_delayed_faded_audio_command(self):
        command = build_audio_command("video.mp4", [self.track], "final.mp4", 5)
        joined = " ".join(command)
        self.assertIn("adelay=delays=1250:all=1", joined)
        self.assertIn("afade=t=in:st=0:d=0.200000", joined)
        self.assertIn("afade=t=out:st=2.600000:d=0.400000", joined)
        self.assertIn("-c:v copy", joined)
        self.assertIn("[aout]", joined)

    def test_loop_track_adds_stream_loop(self):
        track = {**self.track, "loop": True}
        command = build_audio_command("video.mp4", [track], "final.mp4", 5)
        self.assertIn("-stream_loop", command)
        self.assertIn("-1", command)

    def test_multiple_tracks_are_mixed(self):
        command = build_audio_command(
            "video.mp4", [self.track, {**self.track, "source": "/tmp/music.mp3"}],
            "final.mp4", 5
        )
        joined = " ".join(command)
        self.assertIn("amix=inputs=2", joined)
        self.assertIn("[1:a]", joined)
        self.assertIn("[2:a]", joined)


if __name__ == "__main__":
    unittest.main()
