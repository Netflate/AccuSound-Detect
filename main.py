import multiprocessing
import time
import random
import pyaudio
from sound import listen_for_sound_process
from queue import Empty


def finding_the_input_device_index():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"ID: {info['index']}, Name: {info['name']}")
    device_index = int(input("Enter the audio input device ID: "))
    return device_index

def send_command(command):
    # your command
    # This code is about sound detecting, not commands
    # mine was interactive with AHK
    pass


def main():
    x = 1300
    y = 500
    sounds = [
        ##########    IMPORTANT   #########
        # Add here sounds you want the code to detect
        # Second slot corresponds to stop-sound, which will abort the whole code, if detected
        ("sounds/discordB.wav", "sounds/discordS.wav"),
        ("sounds/discordC.wav", "sounds/discordS.wav"),
    ]
    device_index = finding_the_input_device_index()

    queue = multiprocessing.Queue()
    control_queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        target=listen_for_sound_process,
        args=(queue, control_queue, sounds, device_index)
    )
    process.start()

    i = 0
    current_sound = None
    sound_change_confirmed = False

    while True:
        control_queue.put({'index': i})
        timeout = time.time() + random.uniform(3, 5)  # Timeout 4-6 seconds

        while not sound_change_confirmed and time.time() < timeout:
            try:
                message = queue.get_nowait()
                if isinstance(message, dict) and message.get('type') == 'SOUND_CHANGED':
                    current_sound = sounds[i][0]
                    sound_change_confirmed = True
                    print(f"Main process confirmed sound change to {current_sound}")
                    break
            except Empty:
                time.sleep(random.uniform(0.08, 0.15))
                continue

        if not sound_change_confirmed:
            print("Failed to confirm sound change")
            return

        sound_change_confirmed = False
        time.sleep(random.uniform(0.1, 1))

        while True:
            if current_sound == "sounds/discordC.wav":
                send_command(f"click({x},{y})")
                time.sleep(random.uniform(0.8, 1))
            if current_sound == "sounds/discordB.wav":
                send_command("hold_space")
                time.sleep(random.uniform(0.08, 0.15))

            try:
                message = queue.get_nowait()
                if message == "STOP":
                    print("Stop sound detected. Terminating program.")
                    send_command("stop")
                    time.sleep(random.uniform(0.08, 0.15))
                    process.terminate()
                    return
                elif isinstance(message, dict):
                    if message['type'] == 'DETECTED1':
                        print(f"Detected {message['path']} for the first time")
                        if message['path'] == "sounds/discordC.wav":
                            x += 200
                    elif message['type'] == 'DETECTED2':
                        print(f"Detected {message['path']} twice, moving to next sound...")
                        if message['path'] == "sounds/discordC.wav":
                            x -= 200
                        if message['path'] == "sounds/discordB.wav":
                            send_command("stop_holding")
                        break
            except Empty:
                pass

            time.sleep(random.uniform(0.008, 0.02))

        i = (i + 1) % len(sounds)
        time.sleep(random.uniform(0.08, 0.15))


if __name__ == "__main__":
    main()