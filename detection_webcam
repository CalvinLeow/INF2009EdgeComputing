import cv2
import time
import paho.mqtt.client as mqtt
from inference_sdk import InferenceHTTPClient
import threading
import base64

# MQTT Broker details
MQTT_BROKER = "localhost"  # Update with your MQTT broker IP
MQTT_PORT = 1883
PM_STATUS_TOPIC = "sensor/pm_status"
NOISE_STATUS_TOPIC = "sensor/noise_status"
REPORT_TOPIC = "sensor/report"
GET_PICTURE_TOPIC = "topic/getPicture"
PICTURE_TOPIC = "sensor/picture"

# Initialize Roboflow Inference Client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="oh9hNBTlYsNEEKdFRg2I"  # Replace with your API key
)

# Model IDs
HEADPHONE_MODEL_ID = "1-mcruc/3"
MASK_MODEL_ID = "mask-wearing/18"

# Setup Raspberry Pi camera
camera = cv2.VideoCapture(0)

# Flags to track detection state
detect_mask = False
detect_headphones = False

def on_message(client, userdata, message):
    """MQTT Callback function that updates detection states based on sensor data."""
    global detect_mask, detect_headphones
    topic = message.topic
    payload = message.payload.decode("utf-8")
    
    if topic == PM_STATUS_TOPIC:
        if payload == "HIGH":
            print("High pollution detected! Starting continuous mask detection...")
            detect_mask = True
        elif payload == "LOW":
            print("Pollution levels are normal. Stopping mask detection.")
            detect_mask = False
    
    elif topic == NOISE_STATUS_TOPIC:
        if payload == "HIGH":
            print("High noise detected! Starting continuous headphone detection...")
            detect_headphones = True
        elif payload == "LOW":
            print("Noise levels are normal. Stopping headphone detection.")
            detect_headphones = False
    
    elif topic == GET_PICTURE_TOPIC:
        print("Received request to capture an image.")
        capture_and_publish_image()

def capture_image():
    """Captures an image from the Raspberry Pi camera and saves it."""
    ret, frame = camera.read()
    if ret:
        image_path = "captured_image.jpg"
        cv2.imwrite(image_path, frame)
        return image_path, frame
    else:
        print("Error capturing image from camera!")
        return None, None

def capture_and_publish_image():
    """Captures an image and publishes it to the sensor/picture topic."""
    image_path, image_frame = capture_image()
    if image_frame is not None:
        _, buffer = cv2.imencode('.jpg', image_frame)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        client.publish(PICTURE_TOPIC, encoded_image)
        print("Image published to MQTT topic: sensor/picture")

def detect_object(image_path, model_id):
    """Runs object detection using the specified Roboflow model."""
    if image_path:
        result = CLIENT.infer(image_path, model_id=model_id)

        # Ensure 'predictions' exist and is not empty
        if result.get('predictions') and len(result['predictions']) > 0:
            return result['predictions'][0]['class']  # Extracts the first detected class
        
        return "No detection"  # Return this if nothing is detected
    
    return "No detection"

def publish_screenshot(image_frame):
    """Encodes and publishes a screenshot to the MQTT topic if 'no-mask' or 'no-headset' detected."""
    _, buffer = cv2.imencode('.jpg', image_frame)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    client.publish(REPORT_TOPIC, encoded_image)
    print("Screenshot published to MQTT topic: report")

def detection_loop():
    """Continuously detects while thresholds remain high."""
    while True:
        if detect_mask or detect_headphones:
            image_path, image_frame = capture_image()
            print("Camera captured image.")
            
            mask_result = detect_object(image_path, MASK_MODEL_ID) if detect_mask else "No detection"
            headphone_result = detect_object(image_path, HEADPHONE_MODEL_ID) if detect_headphones else "No detection"
            
            print("Mask Detection Result:", mask_result)
            print("Headphone Detection Result:", headphone_result)
            
            # Publish screenshot if 'no-mask' or 'no-headset' is detected
            if mask_result == "no-mask" or headphone_result == "no-headset":
                publish_screenshot(image_frame)

        time.sleep(1)  # Adjust as needed

# MQTT Setup
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe([(PM_STATUS_TOPIC, 0), (NOISE_STATUS_TOPIC, 0), (GET_PICTURE_TOPIC, 0)])

print("Waiting for sensor data...")

# Start detection loop in a separate thread
threading.Thread(target=detection_loop, daemon=True).start()

client.loop_forever()
