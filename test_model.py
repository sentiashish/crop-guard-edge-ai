import numpy as np
from ai_edge_litert.interpreter import Interpreter

MODEL_PATH = "models/crop_raider_model.tflite"

# Load the trained model
interpreter = Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

# Get model input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("Crop Raider model loaded successfully!")

print("\nInput details:")
print(input_details[0]["shape"])
print(input_details[0]["dtype"])

print("\nOutput details:")
print(output_details[0]["shape"])
print(output_details[0]["dtype"])