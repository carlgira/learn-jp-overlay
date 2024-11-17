# Learn Japanese Overlay

A macOS overlay window for learning Japanese. Right now it supports the snes chrono trigger game.

## Setup
```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Run the app
```bash
source .venv/bin/activate
python app.py
```
After running the app open OpenEMU and put it at the right of the screen.

## Instructions
The overlay is prepared to capture the text only of the bottom screen of the SNES. (make sure to move the text down before capturing)

- Press `T` to translate the text.
- And after the translation is done, press `P` to play the audio.


## Generate game scripts and audio (not necessary to run, already generated)
This will generate the scripts and audio for the game. The dictionary and the audios can take lots of time.
```bash
cd scripts
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export OPENAI_API_KEY="your-api-key"
python gen.py
```
