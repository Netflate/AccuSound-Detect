import pyaudio
import numpy as np
import librosa
import time
from scipy import signal
from queue import Empty


class SoundDetector:
    def __init__(self, sounds_config, device_index):
        self.sounds = []
        self.current_sound_index = 0
        self.samplerate = 44100
        self.channels = 1
        self.chunk = 1024
        self.buffer_size = int(self.samplerate * 0.25)
        self.device_index = device_index

        # Load and preprocess all sounds
        for target_path, stop_path in sounds_config:
            target_sound = self._load_and_process_sound(target_path)
            stop_sound = self._load_and_process_sound(stop_path)
            self.sounds.append({
                'target': target_sound,
                'stop': stop_sound,
                'path': target_path
            })

        # Setup audio processing parameters
        nyquist = self.samplerate / 2
        low_freq = 200
        high_freq = 4000
        self.b, self.a = signal.butter(4, [low_freq / nyquist, high_freq / nyquist], btype='band')

        self.detection_threshold = 0.4
        self.min_time_between_detections = 0.5
        self.last_detection_time = 0
        self.detected_count = 0
        self.sound_start_time = time.time()

    def _load_and_process_sound(self, sound_path):
        y, sr = librosa.load(sound_path, sr=44100, mono=True)
        y = y / np.max(np.abs(y))
        threshold = 0.1
        mask = np.abs(y) > threshold
        start = np.where(mask)[0][0]
        end = np.where(mask)[0][-1]
        return y[start:end]

    def preprocess_audio(self, audio):
        filtered = signal.filtfilt(self.b, self.a, audio)
        return filtered / (np.max(np.abs(filtered)) + 1e-6)

    def listen(self, queue, control_queue):
        print("Starting to listen to the stream...")

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.samplerate,
            input=True,
            frames_per_buffer=self.chunk,
            input_device_index=self.device_index
        )

        audio_buffer = np.zeros(self.buffer_size)

        try:
            while True:
                # Check commands from control_queue
                try:
                    command = control_queue.get_nowait()
                    if isinstance(command, dict) and 'index' in command:
                        self.current_sound_index = command['index']
                        self.detected_count = 0
                        self.sound_start_time = time.time()
                        current_path = self.sounds[self.current_sound_index]['path']
                        # Send confirmation about sound change
                        sound_changed_msg = {
                            'type': 'SOUND_CHANGED',
                            'index': self.current_sound_index,
                            'path': current_path
                        }
                        queue.put(sound_changed_msg)
                        print(f"Detector switched to sound {current_path}")
                except Empty:
                    pass

                try:
                    current_sound = self.sounds[self.current_sound_index]
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    new_audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                    audio_buffer = np.roll(audio_buffer, -self.chunk)
                    audio_buffer[-self.chunk:] = new_audio
                    processed_buffer = self.preprocess_audio(audio_buffer)
                    current_time = time.time()

                    # Check target sound
                    correlation = signal.correlate(processed_buffer, current_sound['target'],
                                                   mode='valid', method='fft')
                    correlation /= (len(current_sound['target']) *
                                    np.sqrt(np.mean(processed_buffer ** 2) *
                                            np.mean(current_sound['target'] ** 2)))
                    max_corr = np.max(np.abs(correlation))

                    # Check stop sound
                    stop_correlation = signal.correlate(processed_buffer, current_sound['stop'],
                                                        mode='valid', method='fft')
                    stop_correlation /= (len(current_sound['stop']) *
                                         np.sqrt(np.mean(processed_buffer ** 2) *
                                                 np.mean(current_sound['stop'] ** 2)))
                    stop_max_corr = np.max(np.abs(stop_correlation))

                    if stop_max_corr > self.detection_threshold:
                        queue.put("STOP")
                        break

                    # Process sound detection
                    if (max_corr > self.detection_threshold and
                            (current_time - self.last_detection_time) > self.min_time_between_detections):
                        self.detected_count += 1
                        print(f"Sound detected {current_sound['path']}! Counter: {self.detected_count}")
                        self.last_detection_time = current_time

                        if self.detected_count == 1:
                            queue.put({
                                'type': 'DETECTED1',
                                'path': current_sound['path']
                            })
                            self.sound_start_time = current_time
                        if self.detected_count >= 2:
                            queue.put({
                                'type': 'DETECTED2',
                                'path': current_sound['path']
                            })
                            self.detected_count = 0
                            self.sound_start_time = current_time

                    # Check for automatic sending
                    else:
                        sound_name = current_sound['path'].lower()
                        if ('discordb' in sound_name or 'discordc' in sound_name):
                            auto_interval = 12 if 'discordb' in sound_name else 4
                            time_since_start = current_time - self.sound_start_time

                            if self.detected_count == 0 and time_since_start > auto_interval:
                                print(
                                    f"Automatic DETECTED1 for {current_sound['path']} (passed {time_since_start:.1f} sec)")
                                queue.put({
                                    'type': 'DETECTED1',
                                    'path': current_sound['path']
                                })
                                self.detected_count = 1
                            elif self.detected_count == 1 and time_since_start > (auto_interval * 2):
                                print(f"Automatic DETECTED2 for {current_sound['path']}")
                                queue.put({
                                    'type': 'DETECTED2',
                                    'path': current_sound['path']
                                })
                                self.detected_count = 0
                                self.sound_start_time = current_time

                    time.sleep(0.01)

                except KeyboardInterrupt:
                    print("\nShutting down...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    continue

        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()


def listen_for_sound_process(queue, control_queue, sounds_config, device_index):
    detector = SoundDetector(sounds_config, device_index)
    detector.listen(queue, control_queue)