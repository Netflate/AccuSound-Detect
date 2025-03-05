# AccuSound-Detect

A Python-based application for real-time sound detection and automated response actions.

## Overview

AccuSound-Detect is designed to monitor audio input for specific sounds and trigger custom actions when those sounds are detected. The core functionality includes:

- Real-time audio monitoring from your system
- Detection of pre-defined sound patterns
- Automatic transition between sound detection states
- Customizable timeout periods for sound detection
- Flexible action execution when sounds are detected

## How It Works

### Sound Detection Logic

The application continuously samples audio from your selected input device and processes it through an audio recognition algorithm. It:

1. Captures audio stream data from the specified input device
2. Analyzes the audio against a library of pre-defined sound signatures
3. Calculates confidence levels for each potential match
4. Triggers actions when confidence exceeds the defined threshold
5. Automatically transitions to the next sound to detect
6. Implements timeout logic to handle cases when sounds aren't detected

The original code was designed to cycle through a sequence of sounds, executing specific actions upon detection of each sound or when detection timeouts occur. This sequential detection flow can be easily modified to implement custom logic for your specific use case.

## Audio Setup Requirements

For the application to work correctly, you need to properly configure your audio input source. There are two main approaches:

### Option 1: Stereo Mixer (More Complex)

Using your system's Stereo Mixer allows the application to listen to all system audio. However:
- This captures all system sounds
- Can be more difficult to configure properly
- Requires identifying the correct device index in the code

### Option 2: Voicemeeter Banana + Cable Input (Recommended)

This approach is more flexible and easier to set up:
1. Download and install [Voicemeeter Banana](https://vb-audio.com/Voicemeeter/banana.htm)
2. Install the Virtual Audio Cable driver
3. Configure specific applications to output through Voicemeeter
4. Set the application to listen on the appropriate virtual input

This method allows you to select which applications to monitor rather than capturing all system audio.

## Installation and Usage

### Prerequisites

```
pip install numpy scipy pyaudio librosa
```

### Running the Application

1. Clone the repository
```bash
git clone https://github.com/Netflate/AccuSound-Detect.git
cd AccuSound-Detect
```

2. Create a `sounds` folder in the project directory
```bash
mkdir sounds
```

3. Add your sound files to the `sounds` folder (WAV format recommended)

4. Configure the device index in the code to match your audio input device

5. Run the application
```bash
python main.py
```

## Adding Custom Sounds

To add new sounds for detection:

1. Place audio files in the `sounds` folder
2. The system will automatically load them when starting
3. Format your sounds as high-quality WAV files for best results

## Customizing the Logic

The original code transitions between different sounds with timeout logic.
Command sending code wasn't added to project, it is unnecessary.
You can modify this behavior by:

1. Removing the sound transition code
2. Implementing your custom action logic in the detection handlers
3. Adding conditional logic based on which sound was detected
4. Creating your own response mechanisms for specific audio triggers


