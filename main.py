"""Offline live crop-raider detection for Raspberry Pi 5."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ai_edge_litert.interpreter import Interpreter
from gpiozero import LED, Buzzer


CLASS_NAMES = [
    "Armadilles",
    "Bear",
    "Birds",
    "Cow",
    "Crocodile",
    "Deer",
    "Elephant",
    "Goat",
    "Horse",
    "Jaguar",
    "Monkey",
    "Rabbit",
    "Skunk",
    "Tiger",
    "Wild Boar",
]
MODEL_PATH = Path("models/crop_raider_model.tflite")
SNAPSHOT_DIR = Path("snapshots")
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
INPUT_WIDTH = 224
INPUT_HEIGHT = 224
CONFIDENCE_THRESHOLD = 0.70
ALARM_COOLDOWN_SECONDS = 10.0
BUZZER_GPIO = 18
LED_RELAY_GPIO = 23

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
LOGGER = logging.getLogger("crop-raider")


def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """Convert an OpenCV BGR frame to the model's float32 NCHW input."""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb_frame, (INPUT_WIDTH, INPUT_HEIGHT))
    normalized = resized.astype(np.float32) / 255.0
    return np.expand_dims(np.transpose(normalized, (2, 0, 1)), axis=0)


def classify(interpreter: Any, input_details: list[dict[str, Any]],
             output_details: list[dict[str, Any]], frame: np.ndarray) -> tuple[str, float]:
    """Run one inference and return the highest scoring class and probability."""
    input_tensor = preprocess_frame(frame)
    expected_shape = tuple(input_details[0]["shape"])
    if input_tensor.shape != expected_shape:
        raise ValueError(
            f"Model expects input shape {expected_shape}, but preprocessing produced "
            f"{input_tensor.shape}. Verify the exported model format."
        )

    interpreter.set_tensor(input_details[0]["index"], input_tensor)
    interpreter.invoke()
    scores = np.asarray(interpreter.get_tensor(output_details[0]["index"])[0])
    if scores.size != len(CLASS_NAMES):
        raise ValueError(
            f"Model returned {scores.size} scores; expected {len(CLASS_NAMES)} classes."
        )

    predicted_index = int(np.argmax(scores))
    return CLASS_NAMES[predicted_index], float(scores[predicted_index])


def save_snapshot(frame: np.ndarray, animal: str) -> Path:
    """Save a timestamped detection frame and return its path."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    safe_animal = animal.lower().replace(" ", "_")
    snapshot_path = SNAPSHOT_DIR / f"{timestamp}_{safe_animal}.jpg"
    if not cv2.imwrite(str(snapshot_path), frame):
        raise OSError(f"Could not write snapshot to {snapshot_path}")
    return snapshot_path


def trigger_alarm(buzzer: Buzzer, led_relay: LED, frame: np.ndarray,
                  animal: str, confidence: float) -> None:
    """Activate outputs briefly and persist the frame for a valid detection."""
    buzzer.on()
    led_relay.on()
    try:
        snapshot_path = save_snapshot(frame, animal)
        LOGGER.warning(
            "ALERT: %s (%.1f%%); snapshot saved to %s",
            animal,
            confidence * 100,
            snapshot_path,
        )
    finally:
        buzzer.off()
        led_relay.off()


def main() -> None:
    """Open the camera and run continuous offline inference."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"LiteRT model not found: {MODEL_PATH}")

    interpreter = Interpreter(model_path=str(MODEL_PATH))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    if not input_details or not output_details:
        raise RuntimeError("LiteRT model does not expose input and output tensors.")

    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    if not camera.isOpened():
        raise RuntimeError(f"Could not open USB webcam at index {CAMERA_INDEX}.")

    buzzer = Buzzer(BUZZER_GPIO)
    led_relay = LED(LED_RELAY_GPIO)
    last_alarm_time = -ALARM_COOLDOWN_SECONDS
    LOGGER.info("Crop Raider Alert System started. Press q in the preview to stop.")

    try:
        while True:
            success, frame = camera.read()
            if not success or frame is None:
                raise RuntimeError("Failed to read a frame from the USB webcam.")

            animal, confidence = classify(
                interpreter, input_details, output_details, frame
            )
            now = time.monotonic()
            valid_detection = confidence >= CONFIDENCE_THRESHOLD
            cooldown_ready = now - last_alarm_time >= ALARM_COOLDOWN_SECONDS

            if valid_detection:
                LOGGER.info("Detection: %s (%.1f%%)", animal, confidence * 100)
                if cooldown_ready:
                    trigger_alarm(buzzer, led_relay, frame, animal, confidence)
                    last_alarm_time = now

            display_text = f"{animal}: {confidence * 100:.1f}%"
            color = (0, 0, 255) if valid_detection else (0, 200, 200)
            cv2.putText(
                frame, display_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, color, 2, cv2.LINE_AA,
            )
            cv2.imshow("Crop Raider Alert System", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        buzzer.off()
        led_relay.off()
        buzzer.close()
        led_relay.close()
        LOGGER.info("Crop Raider Alert System stopped.")


if __name__ == "__main__":
    main()
