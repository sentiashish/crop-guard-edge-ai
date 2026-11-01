# Raspberry Pi 5 Setup Guide

## 1. Flash Raspberry Pi OS

1. Install **Raspberry Pi Imager** from the official Raspberry Pi website.
2. Insert a reliable microSD card and select **Raspberry Pi 5**.
3. Select **Raspberry Pi OS (64-bit)** based on Bookworm.
4. In the Imager customisation screen, configure the hostname, user, password, Wi-Fi, timezone, and SSH if the device will be administered remotely.
5. Write and verify the image, insert the card into the Pi, connect the webcam and network, and boot.

## 2. Update the operating system

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3-venv python3-dev python3-opencv v4l-utils git
sudo reboot
```

Check the webcam:

```bash
v4l2-ctl --list-devices
```

## 3. Install the application

```bash
git clone https://github.com/sentiashish/crop-guard-edge-ai.git
cd crop-guard-edge-ai
python3 -m venv --system-site-packages cropenv
source cropenv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
test -f models/crop_raider_model.tflite
```

The `--system-site-packages` option allows the virtual environment to use the Raspberry Pi's packaged OpenCV build. If the device uses a different OpenCV installation, install a compatible wheel instead.

## 4. Wire the outputs

Power down the Pi before wiring. Connect the active buzzer signal to **GPIO 18 (physical pin 12)** and the LED relay signal to **GPIO 23 (physical pin 16)**. Connect grounds together. Use the module's specified supply voltage and a transistor, driver, or opto-isolated relay where the load requires more current than a GPIO can provide. Never connect a high-current LED or motor directly to a GPIO.

The application assumes both modules are active-high. If a relay is active-low, configure the relay module or adapt the output driver safely rather than changing the confidence logic.

## 5. Run and test

```bash
source cropenv/bin/activate
python main.py
```

The preview displays the top class and confidence. A prediction at or above 70% activates both outputs and writes a timestamped image to `snapshots/`. Predictions below 70% are displayed but do not activate the alarm. Press `q` to stop; `Ctrl+C` also performs GPIO and camera cleanup.

## 6. Operational checklist

- Confirm the camera has a clear view and sufficient night lighting.
- Test the buzzer and relay at low risk before leaving the system unattended.
- Confirm the model's input layout is NCHW and that its output contains exactly 15 scores.
- Review snapshots and tune the threshold/cooldown only after collecting field data.
- Keep the model and application on local storage; the runtime does not require internet access.
