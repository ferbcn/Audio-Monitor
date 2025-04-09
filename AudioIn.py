import pyaudio
import numpy as np

WIDTH = 2
# CHUNK = 2048
# FORMAT = pyaudio.paInt32


class AudioIn:
    def __init__(self, chunk=1024, sample_rate=44100):
        self.p = pyaudio.PyAudio()
        self.chunk = chunk
        self.audio = np.empty(chunk, dtype="int16")

    def __del__(self):
        self.p.terminate()

    def callback(self, in_data, frame_count, time_info, status):
        self.audio = np.fromstring(in_data, dtype=np.int16)
        return (in_data, pyaudio.paContinue)

    def start_stream(self, rate=44100, chunk=44100, output=False, device=None, output_device=None, channels=1):
        try:
            self.stream = self.p.open(format=self.p.get_format_from_width(WIDTH),
                                      channels=channels,
                                      rate=rate,
                                      input=True,
                                      output=output,
                                      stream_callback=self.callback,
                                      input_device_index=device,
                                      output_device_index=output_device,
                                      frames_per_buffer=chunk)
            self.stream.start_stream()
        except Exception as e:
            print(f"Error selecting audio device: {e}!")

    def stop_stream(self):
        self.stream.stop_stream()
        self.stream.close()

    def get_all_devices_info(self):
        device_count = self.p.get_device_count()
        devices_info = []
        for i in range(device_count):
            try:
                device_info = self.p.get_device_info_by_host_api_device_index(0, i)
                devices_info.append(device_info)
            except Exception as e:
                print(e)
        return devices_info

    def get_input_devices_info(self):
        device_count = self.p.get_device_count()
        devices_info = []
        for i in range(device_count):
            try:
                device_info = self.p.get_device_info_by_host_api_device_index(0, i)
                if int(device_info.get('maxInputChannels')) > 0:
                    devices_info.append(device_info)
            except Exception as e:
                pass
        return devices_info

    def get_output_devices_info(self):
        device_count = self.p.get_device_count()
        devices_info = []
        for i in range(device_count):
            try:
                device_info = self.p.get_device_info_by_host_api_device_index(0, i)
                if int(device_info.get('maxOutputChannels')) > 0:
                    devices_info.append(device_info)
            except Exception as e:
                pass
        return devices_info

    def get_default_input_device(self):
        return self.p.get_default_input_device_info()

    def get_default_output_device(self):
        return self.p.get_default_output_device_info()


if __name__ == '__main__':
    myAudio = AudioIn()
    devices = myAudio.get_all_devices_info()
    for device in devices:
        print (device)
    default = myAudio.get_default_input_device().get('index')
    print(f'Default Input: {default}')
    default = myAudio.get_default_output_device().get('index')
    print(f'Default Output: {default}')