import pathlib
import sys
from unittest.mock import MagicMock

sys.modules["picamera2"] = MagicMock()
sys.modules["picamera2.encoders"] = MagicMock()
sys.modules["picamera2.outputs"] = MagicMock()

import obs_picamera.recorder as rec  # noqa E402 # isort: skip


def test_recorder_init(tmp_path: pathlib.Path) -> None:
    rec.Picamera2 = MagicMock()
    rec.CircularOutput = MagicMock()
    rec.H264Encoder = MagicMock()
    recorder = rec.Recorder()
    recorder.save_snippet_to(tmp_path)
    assert recorder.output.fileoutput == tmp_path
