import asyncio
import json
import logging
import os
from pathlib import Path

import toml
from fastapi import FastAPI, Response

from obs_picamera.bluetooth import ObsBT, ObsScannerError
from obs_picamera.recorder import Recorder

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger()

recorder = Recorder()


# flake8: noqa
def main() -> FastAPI:
    app = FastAPI()

    obsbt = ObsBT()

    @app.get("/v1/preview.jpeg")
    async def preview() -> Response:
        return Response(recorder.jpeg_screenshot(), media_type="image/jpeg")

    def record_callback(**kwargs) -> None:  # type: ignore # pragma: no cover
        target_dir = Path("recordings") / kwargs["track_id"]
        target_dir.mkdir(parents=True, exist_ok=True)
        recorder.save_snippet_to(
            open(target_dir / f"{kwargs['sensortime']}.h264", "wb")
        )
        toml.dump(
            {str(target_dir / f"{kwargs['sensortime']}.h264"): kwargs},
            open(target_dir / "events.toml", "a"),
        )
        logger.info(f"saved to {target_dir}")

    obsbt.overtaking_callbacks.append(record_callback)

    async def bt_loop() -> None:  # pragma: no cover
        while True:
            try:
                await obsbt.run()
            except ObsScannerError:
                logger.exception("Restarting bluetooth connection")

    @app.on_event("startup")
    async def start_loop() -> None:
        logger.info("starting loop")
        asyncio.create_task(bt_loop())

    @app.get("/v1/history")
    async def history() -> Response:
        return Response(json.dumps(list(obsbt.history)), media_type="application/json")

    @app.get("/v1/state")
    async def state() -> Response:
        [time, left, right] = obsbt.history[-1] if len(obsbt.history) > 0 else [0, 0, 0]
        return Response(
            json.dumps(
                {
                    "sensortime": time,
                    "distance_l": left,
                    "distance_r": right,
                    "track": obsbt.track_id,
                    "handlebar_size": (obsbt.handlebar_left, obsbt.handlebar_right),
                    "connected": obsbt.bt_connected,
                }
            ),
            media_type="application/json",
        )

    @app.get("/v1/tracks")
    async def tracks() -> Response:
        dirs = os.listdir("recordings")
        return Response(json.dumps(dirs))

    @app.get("/v1/tracks/{id}")
    async def track(id: str) -> Response:
        events_file = Path(f"recordings/{id}") / "events.toml"
        res = toml.load(events_file.open("r"))
        return Response(json.dumps(res), media_type="application/json")

    return app


app = main()
