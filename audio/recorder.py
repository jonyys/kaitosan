import sounddevice as sd
import soundfile as sf


class Recorder:

    def __init__(self, sample_rate=16000):

        self.sample_rate = sample_rate

    def record(self, filename="audio/input.wav"):

        input("Pulsa ENTER para empezar a grabar...")

        print("🎤 Grabando... Pulsa ENTER para terminar.")

        recording = []

        def callback(indata, frames, time, status):
            recording.append(indata.copy())

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=callback,
        ):

            input()

        audio = __import__("numpy").concatenate(recording, axis=0)

        sf.write(filename, audio, self.sample_rate)

        return filename