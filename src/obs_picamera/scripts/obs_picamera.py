import asyncio
import json
import logging
from pathlib import Path

from obs_picamera.bluetooth import ObsBT, ObsScannerError
from obs_picamera.recorder import Recorder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def main() -> None:
    recorder = Recorder()

    def record_callback(**kwargs) -> None:  # type: ignore
        target_dir = Path(kwargs["track_id"])
        target_dir.mkdir(parents=True, exist_ok=True)
        recorder.save_snippet_to(
            open(target_dir / f"{kwargs['sensortime']}.h264", "wb")
        )
        json.dump(kwargs, open(target_dir / f"{kwargs['sensortime']}.json", "w"))

    while True:
        try:
            obsbt = ObsBT()
            asyncio.run(obsbt.run())
            obsbt.overtaking_callbacks.append(record_callback)
        except ObsScannerError:
            logger.exception("Restarting bluetooth connection")
