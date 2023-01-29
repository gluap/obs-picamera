import pathlib

from picamera2 import Picamera2  # type: ignore
from picamera2.encoders import H264Encoder  # type: ignore
from picamera2.outputs import CircularOutput  # type: ignore


class Recorder:
    """
    Recorder for picamera that starts recording to a ring buffer when initialized
    and allows to save the last 5 seconds of video from the buffer.
    """

    def __init__(self) -> None:
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_video_configuration())
        self.encoder = H264Encoder()
        self.output = CircularOutput()
        self.picam2.start_recording(self.encoder, self.output)

    def save_snippet_to(self, filename: pathlib.Path) -> None:
        """
        Save the last 5 seconds of video from the buffer to the filename
        :param filename:
        :return:
        """
        self.output.fileoutput = filename
        self.output.start()
        self.output.stop()

    def __del__(self) -> None:
        self.picam2.stop_recording()
