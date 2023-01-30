from obs_picamera.bluetooth import ObsBT
from obs_picamera.recorder import Recorder
from pathlib import Path
import json


def main():
    obsbt = ObsBT()
    recorder = Recorder()

    def record_callback(**kwargs):
        target_dir = Path(kwargs['track_id'])
        target_dir.mkdir(parents=True, exist_ok=True)
        recorder.save_snippet_to(target_dir / f"{kwargs['sensortime']}.mp4")
        json.dump(kwargs, open(target_dir / f"{kwargs['sensortime']}.json"))

    obsbt.overtaking_callbacks.append(record_callback)
    obsbt.run()
