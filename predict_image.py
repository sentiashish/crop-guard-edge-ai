import cv2
import numpy as np
from ai_edge_litert.interpreter import Interpreter

class_names = [
    "Armadilles", "Bear", "Birds", "Cow", "Crocodile",
    "Deer", "Elephant", "Goat", "Horse", "Jaguar",
    "Monkey", "Rabbit", "Skunk", "Tiger", "Wild Boar"
]
confidence_threshold = 70.0

interpreter = Interpreter(model_path="models/crop_raider_model.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

image = cv2.imread("test_images/download.png")
if image is None:
    raise FileNotFoundError("Could not find test_images/download.png")

image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
image = cv2.resize(image, (224, 224)).astype(np.float32) / 255.0
image = np.expand_dims(np.transpose(image, (2, 0, 1)), axis=0)

interpreter.set_tensor(input_details[0]["index"], image)
interpreter.invoke()
scores = interpreter.get_tensor(output_details[0]["index"])[0]
predicted_index = int(np.argmax(scores))
confidence = float(scores[predicted_index]) * 100
detected_animal = class_names[predicted_index]

print("\n===== CROP RAIDER PREDICTION =====")
if confidence >= confidence_threshold:
    print(f"Animal Detected: {detected_animal}")
    print(f"Confidence: {confidence:.2f}% -> TRIGGER ALARM")
else:
    print(f"Low confidence ({confidence:.2f}% for {detected_animal}) or unknown object.")
    print("Result: Ignored (filtered out by 70% threshold)")