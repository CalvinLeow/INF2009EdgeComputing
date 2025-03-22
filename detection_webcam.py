import cv2
import time
import paho.mqtt.client as mqtt
from inference_sdk import InferenceHTTPClient
import threading
import base64
import json

# MQTT Broker details
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
PM_STATUS_TOPIC = "sensor/pm_status"
PM_ALERT_TOPIC = "sensor/PMAlertMessage"
NOISE_STATUS_TOPIC = "sensor/noise_status"
REPORT_TOPIC = "sensor/report"
GET_PICTURE_TOPIC = "topic/getPicture"
PICTURE_TOPIC = "sensor/picture"

# Initialize Roboflow Inference Client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="oh9hNBTlYsNEEKdFRg2I"
)

# Model IDs
HEADPHONE_MODEL_ID = "1-mcruc/3"
MASK_MODEL_ID = "mask-wearing/18"

# Alert intervals so it doesn't spam user and store readings
latest_pm_reading = 0
last_pm_alert_time = 0
ALERT_INTERVAL = 15  # seconds

# Setup Raspberry Pi camera
camera = cv2.VideoCapture(0)

# Flags to track detection state
detect_mask = False
detect_headphones = False

def on_message(client, userdata, message):
    global detect_mask, detect_headphones, latest_pm_reading
    topic = message.topic
    payload = message.payload.decode("utf-8")
    if topic == PM_STATUS_TOPIC:
        try:
            data = json.loads(payload)
            status = data.get("status", "LOW")
            latest_pm_reading = data.get("pm2_5", 0)
            if status == "HIGH":
                print("High pollution detected! Starting continuous mask detection...")
                detect_mask = True
            else:
                print("Pollution levels are normal. Stopping mask detection.")
                detect_mask = False
        except json.JSONDecodeError:
            print("Error decoding PM_STATUS payload:", payload)
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
    for _ in range(3):
        ret, frame = camera.read()
        time.sleep(0.1)
    if ret:
        frame_resized = cv2.resize(frame, (416, 416))
        image_path = "captured_image.jpg"
        cv2.imwrite(image_path, frame_resized)
        cv2.waitKey(100)
        return image_path, frame_resized
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
            return result['predictions'][0]['class']
        return "No detection"
    return "No detection"

def publish_screenshot(image_frame):
    """Encodes and publishes a screenshot to the MQTT topic if 'no-mask' or 'no-headset' detected."""
    _, buffer = cv2.imencode('.jpg', image_frame)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    client.publish(REPORT_TOPIC, encoded_image)
    print("Screenshot published to MQTT topic: report")

def prepare_and_publish_pm_alert(image_frame):
    global last_pm_alert_time
    current_time = time.time()
    if current_time - last_pm_alert_time >= ALERT_INTERVAL:
        _, buffer = cv2.imencode('.jpg', image_frame)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        alert_payload = {
            "message": "No mask detected while PM2.5 is high!",
            "pm_reading": latest_pm_reading,
            "image": encoded_image
        }
        client.publish(PM_ALERT_TOPIC, json.dumps(alert_payload))
        print("Alert sent to sensor/PMAlertMessage")
        last_pm_alert_time = current_time
    else:
        print("Skipping alert to avoid spamming...")

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
            if detect_mask and mask_result == "no-mask":
                prepare_and_publish_pm_alert(image_frame)
        time.sleep(1)

# MQTT Setup
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe([(PM_STATUS_TOPIC, 0), (NOISE_STATUS_TOPIC, 0), (GET_PICTURE_TOPIC, 0)])

print("Waiting for sensor data...")

# Start detection loop in a separate thread
threading.Thread(target=detection_loop, daemon=True).start()

client.loop_forever()
