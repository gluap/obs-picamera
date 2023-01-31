from typing import BinaryIO

from picamera2 import Picamera2  # type: ignore
from picamera2.encoders import H264Encoder, Quality  # type: ignore
from picamera2.outputs import CircularOutput  # type: ignore


class Recorder:
    """
    Recorder for picamera that starts recording to a ring buffer when initialized
    and allows to save the last 5 seconds of video from the buffer.
    """

    def __init__(self) -> None:
        self.picam2 = Picamera2()
        fps = 25
        dur = 10
        micro = int((1 / fps) * 1000000)
        vconfig = self.picam2.create_video_configuration(
            main={"size": (2048, 1536)}, lores={"size": (800, 606)}, encode="lores"
        )
        vconfig["controls"]["FrameDurationLimits"] = (micro, micro)
        self.picam2.configure(vconfig)
        self.encoder = H264Encoder(
            iperiod=1,
            repeat=True,
        )
        self.output = CircularOutput(
            buffersize=int(fps * (dur + 0.2)), outputtofile=False
        )
        self.picam2.start_recording(self.encoder, self.output, Quality.HIGH)

    def save_snippet_to(self, fp: BinaryIO) -> None:
        """
        Save the last 5 seconds of video from the buffer to the filename
        :param fp:
        :return:
        """
        self.output.fileoutput = fp
        self.output.stop()

    def __del__(self) -> None:
        self.picam2.stop_recording()
