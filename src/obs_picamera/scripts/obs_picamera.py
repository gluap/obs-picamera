import asyncio
import json
import logging
from pathlib import Path

from obs_picamera.bluetooth import ObsBT
from obs_picamera.recorder import Recorder

logging.basicConfig(level=logging.INFO)


def main() -> None:
    obsbt = ObsBT()
    recorder = Recorder()

    def record_callback(**kwargs) -> None:  # type: ignore
        target_dir = Path(kwargs["track_id"])
        target_dir.mkdir(parents=True, exist_ok=True)
        recorder.save_snippet_to(target_dir / f"{kwargs['sensortime']}.mp4")
        json.dump(kwargs, open(target_dir / f"{kwargs['sensortime']}.json"))

    obsbt.overtaking_callbacks.append(record_callback)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(obsbt.run())
