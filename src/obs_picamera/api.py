import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, Response

from obs_picamera.bluetooth import ObsBT, ObsScannerError
from obs_picamera.recorder import Recorder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

recorder = Recorder()


def main() -> FastAPI:
    app = FastAPI()

    obsbt = ObsBT()

    @app.get("/v1/preview.jpeg")
    async def preview() -> Response:
        return Response(recorder.jpeg_screenshot(), media_type="image/jpeg")

    def record_callback(**kwargs) -> None:  # type: ignore # pragma: no cover
        target_dir = Path("/home/pi/recordings") / kwargs["track_id"]
        target_dir.mkdir(parents=True, exist_ok=True)
        recorder.save_snippet_to(
            open(target_dir / f"{kwargs['sensortime']}.h264", "wb")
        )
        json.dump(kwargs, open(target_dir / f"{kwargs['sensortime']}.json", "w"))
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
            json.dumps({"sensortime": time, "distance_l": left, "distance_r": right}),
            media_type="application/json",
        )

    return app


app = main()
