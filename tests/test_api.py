import sys
from unittest.mock import MagicMock

sys.modules["picamera2"] = MagicMock()
sys.modules["picamera2.encoders"] = MagicMock()
sys.modules["picamera2.outputs"] = MagicMock()

from fastapi.testclient import TestClient  # noqa E402 # isort: skip
from obs_picamera.api import app  # noqa E402 # isort: skip

client = TestClient(app)


def test_app() -> None:
    r = client.get("/v1/preview.jpeg")
    client.get("/v1/history")
    client.get("/v1/state")

    assert r.status_code == 200
