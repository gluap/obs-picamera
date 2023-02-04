import pathlib
import sys
from unittest.mock import MagicMock

sys.modules["picamera2"] = MagicMock()
sys.modules["picamera2.encoders"] = MagicMock()
sys.modules["picamera2.outputs"] = MagicMock()

import obs_picamera.recorder as rec  # noqa E402 # isort: skip


def test_recorder_init(tmp_path: pathlib.Path) -> None:
    recorder = rec.Recorder()
    fp = open(tmp_path / "fck", "wb")
    recorder.save_snippet_to(fp)
    recorder.jpeg_screenshot()
    assert recorder.output.fileoutput == fp
