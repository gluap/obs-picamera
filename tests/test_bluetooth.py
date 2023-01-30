import asyncio
import struct
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import obs_picamera.bluetooth  # flake8: noqa

sys.modules["bleak.AdvertisementData"] = MagicMock()
sys.modules["bleak.BleakScanner"] = MagicMock()
sys.modules["bleak.BLEDevice"] = MagicMock()


def test_bluetooth() -> None:
    obs_picamera.bluetooth.timeout_seconds = 0.5

    if sys.version_info < (3, 10):
        asyncio.set_event_loop(obs_picamera.bluetooth.loop)

    with patch("bleak.BleakScanner") as p:
        p.return_value.start = AsyncMock()
        p.return_value.stop = AsyncMock()
        with pytest.raises(obs_picamera.bluetooth.ObsScannerError):
            obsbt = obs_picamera.bluetooth.ObsBT()

    with patch("bleak.BleakScanner") as p:
        scanner = obs_picamera.bluetooth.ObsScanner()
        device = sys.modules["bleak.BLEDevice"]

        scanner.detection_callback(device, sys.modules["bleak.AdvertisementData"])  # type: ignore
        scanner.obs_address = "ffff"

        scanner.unittesting = True

        p.return_value.start = AsyncMock()
        p.return_value.stop = AsyncMock()
        asyncio.run(scanner.run())

        scanner = obs_picamera.bluetooth.ObsScanner()

        scanner.detection_callback(device, sys.modules["bleak.AdvertisementData"])  # type: ignore

        scanner.unittesting = True

        assert scanner.obs_address is not None
        scanner.unittesting = True

        with patch("bleak.BleakClient") as p:
            p.return_value.__aenter__.return_value.read_gatt_char.return_value = (
                struct.pack("hh", 1, 2)
            )
            obsbt = obs_picamera.bluetooth.ObsBT(scanner=scanner)
            obsbt.unittesting = True
            asyncio.run(obsbt.connect())
            obsbt.bt_connected = False
            obsbt.obs_address = "haha"
            asyncio.run(obsbt.run())
