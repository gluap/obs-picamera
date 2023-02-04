import uvicorn


def run() -> None:
    uvicorn.run("obs_picamera.api:app", host="0.0.0.0", port=5000, log_level="info")
