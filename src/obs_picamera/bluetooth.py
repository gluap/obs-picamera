import asyncio
import logging
import struct
import sys
import time
from typing import Callable, List, Optional

import bleak
from bleak.exc import BleakDeviceNotFoundError

SENSOR_DISTANCE_NOTIFICATION_UUID = "1FE7FAF9-CE63-4236-0004-000000000002"
CLOSE_PASS_NOTIFICATION_UUID = "1FE7FAF9-CE63-4236-0004-000000000003"
HANDLEBAR_OFFSET_UUID = "1FE7FAF9-CE63-4236-0004-000000000004"
TRACK_ID_UUID = "1FE7FAF9-CE63-4236-0004-000000000005"

logger = logging.getLogger(__name__)
#
# Blutooth scanner config
#

timeout_seconds: float = 15


class ObsScanner:
    unittesting: bool = False

    def __init__(self) -> None:
        if sys.version_info < (3, 10):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self._scanner = bleak.BleakScanner(detection_callback=self.detection_callback)
        self.obs_address: str | None = None
        self.scanning = asyncio.Event()

    def detection_callback(
        self, device: bleak.BLEDevice, advertisement_data: bleak.AdvertisementData
    ) -> None:
        if device.name.startswith("OpenBikeSensor"):
            logger.info(f"Found OpenBikeSensor {device}")
            self.obs_address = device.address
            self.scanning.clear()

    async def run(self) -> None:
        logger.info("Scan for devices")
        if not self.unittesting:
            self.obs_address = None
        await self._scanner.start()
        self.scanning.set()
        end_time = time.time() + timeout_seconds
        while self.scanning.is_set():
            if time.time() > end_time:
                self.scanning.clear()
                logger.info("Scan has timed out so we terminate")
            await asyncio.sleep(0.1)
        await self._scanner.stop()
        if self.obs_address is None:
            raise ObsScannerError("No OBS found")  # flake8: noqa


class ObsBT:
    def __init__(self, scanner: Optional[ObsScanner] = None) -> None:
        self.bt_connected: bool = False
        self.obs_address: str | None = None
        self.my_scanner: ObsScanner = scanner if scanner is not None else ObsScanner()
        self.find_obs()
        self.handlebar_left: str | None = None
        self.handlebar_right: str | None = None
        self.track_id: str | None = None
        self.overtaking_callbacks: List[Callable] = []
        self.recording_callbacks: List[Callable] = []
        self.bt_connecting: bool = False
        self.unittesting: bool = False

    def find_obs(self) -> None:
        asyncio.run(self.my_scanner.run())
        self.obs_address = self.my_scanner.obs_address
        assert self.obs_address is not None

    def overtaking_handler(self, sender: str, data: bytearray) -> None:
        """Simple notification handler which prints the data received."""
        t, l, r = struct.unpack("Ihh", data)
        logger.info(f"sensortime: {t}, Left distance {l}, right distance {r}")
        for callback in self.overtaking_callbacks:
            callback(
                distance_l=l - self.handlebar_left,
                distance_r=r - self.handlebar_right,
                handlebars_l=self.handlebar_left,
                handlebar_r=self.handlebar_right,
                track_id=self.track_id,
                sensortime=t,
            )

    async def connect(self) -> None:
        def disconnected_callback(client: bleak.BleakClient) -> None:
            logger.info("DISCONNECTED")
            self.bt_connected = False

        async with bleak.BleakClient(
            self.obs_address, disconnected_callback=disconnected_callback, timeout=25  # type: ignore
        ) as client:
            logger.info(f"Connected: {client.is_connected}")
            await client.start_notify(
                CLOSE_PASS_NOTIFICATION_UUID, self.overtaking_handler
            )
            self.track_id = (await client.read_gatt_char(TRACK_ID_UUID)).decode("utf-8")
            handlebar = await client.read_gatt_char(HANDLEBAR_OFFSET_UUID)
            self.handlebar_left, self.handlebar_right = struct.unpack("hh", handlebar)
            logger.info(
                f"track id is {self.track_id}, handlebar: <{self.handlebar_left} | {self.handlebar_right} >"
            )
            self.bt_connected = True
            self.bt_connecting = False
            while True:
                if not self.bt_connected or self.unittesting:
                    break
                await asyncio.sleep(1)

    async def run(self) -> None:
        while not self.bt_connected:
            try:
                if not self.bt_connecting:
                    logger.info(f"connecting to {self.obs_address}")
                    self.bt_connecting = True
                    assert isinstance(self.obs_address, str)
                    await self.connect()
                else:
                    await asyncio.sleep(1)
            except BleakDeviceNotFoundError:
                logger.info(
                    f"lost connection, reconnecting. connecting={self.bt_connecting}"
                )


class ObsScannerError(Exception):
    pass


if __name__ == "__main__":  # pragma: no cover
    while True:
        try:
            obsbt = ObsBT()
            asyncio.run(obsbt.run())
        except (ObsScannerError, bleak.BleakError):
            logger.exception("ERROR. Retry")
