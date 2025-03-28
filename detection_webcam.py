import cv2
import time
import paho.mqtt.client as mqtt
import threading
import base64
import json
import numpy as np
from tensorflow.keras.models import load_model
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# MQTT Broker details
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
PM_STATUS_TOPIC = "sensor/pm_status"
PM_ALERT_TOPIC = "sensor/PMAlertMessage"
NOISE_STATUS_TOPIC = "sensor/noise_status"
REPORT_TOPIC = "sensor/report"
GET_PICTURE_TOPIC = "topic/getPicture"
PICTURE_TOPIC = "sensor/picture"
GET_GRAPH_TOPIC = "topic/getGraph/camera"

# Alert interval settings
latest_pm_reading = 0
last_pm_alert_time = 0
ALERT_INTERVAL = 15  # seconds

# Camera setup
camera = cv2.VideoCapture(0)

# Detection flags
detect_mask = False
detect_headphones = False

# Load models
mask_model = load_model("mask_detector.keras")
earmuff_model = load_model("earmuff_detector.keras")

# Load OpenCV HOG person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# CSV file to store violations
CSV_FILE = "violations.csv"

# Check if the file exists and write headers if it's a new file
def initialize_csv():
    try:
        with open(CSV_FILE, mode='r', newline='') as file:
            pass  # File exists
    except FileNotFoundError:
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "violation_type"])  # Headers

initialize_csv()

# Function to add violation to CSV
def add_violation(violation_type):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, violation_type])

# Helper function to generate graph
def generate_violation_graph():
    # Read the CSV into a pandas DataFrame
    df = pd.read_csv(CSV_FILE)

    # Separate the data based on violation type
    no_mask_df = df[df['violation_type'] == 'no_mask']
    no_earmuff_df = df[df['violation_type'] == 'no_earmuff']

    # Create a plot
    plt.figure(figsize=(10,6))

    # Plot no mask violations
    plt.plot(no_mask_df['timestamp'], [1] * len(no_mask_df), 'ro', label="No Mask Violations")

    # Plot no earmuff violations
    plt.plot(no_earmuff_df['timestamp'], [1] * len(no_earmuff_df), 'bo', label="No Earmuff Violations")

    plt.xticks(rotation=45)
    plt.xlabel("Time")
    plt.ylabel("Violations")
    plt.title("Violations Graph")
    plt.legend()

    plt.tight_layout()

    # Save the plot to a file
    plt.savefig("/tmp/violation_graph.png")
    plt.close()

# MQTT callback
def on_message(client, userdata, message):
    global detect_mask, detect_headphones, latest_pm_reading
    topic = message.topic
    payload = message.payload.decode("utf-8")

    if topic == PM_STATUS_TOPIC:
        try:
            data = json.loads(payload)
            status = data.get("status", "LOW")
            latest_pm_reading = data.get("pm2_5", 0)
            detect_mask = status == "HIGH"
            print("PM2.5 status:", "HIGH - Mask detection ON" if detect_mask else "LOW - Mask detection OFF")
        except json.JSONDecodeError:
            print("Error decoding PM_STATUS payload:", payload)

    elif topic == NOISE_STATUS_TOPIC:
        detect_headphones = payload == "HIGH"
        print("Noise detection:", "ON" if detect_headphones else "OFF")

    elif topic == GET_PICTURE_TOPIC:
        print("Received request to capture an image.")
        capture_and_publish_image()

    elif topic == GET_GRAPH_TOPIC:
        print("Received request for violation graph")
        generate_violation_graph()

        # Send graph as image
        with open("/tmp/violation_graph.png", "rb") as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
            client.publish("sensor/violation_graph", encoded_image)
            print("Published violation graph to topic:", "sensor/violation_graph")

# Capture and resize image
def capture_image():
    for _ in range(3):
        ret, frame = camera.read()
        time.sleep(0.1)
    if ret:
        frame_resized = cv2.resize(frame, (416, 416))
        cv2.imwrite("captured_image.jpg", frame_resized)
        return "captured_image.jpg", frame_resized
    else:
        print("Error capturing image!")
        return None, None

# Publish image to MQTT
def capture_and_publish_image():
    image_path, image_frame = capture_image()
    if image_frame is not None:
        _, buffer = cv2.imencode('.jpg', image_frame)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        client.publish(PICTURE_TOPIC, encoded_image)
        print("Published image to topic:", PICTURE_TOPIC)

# Person detection using OpenCV HOG
def detect_person(image_frame):
    gray = cv2.cvtColor(image_frame, cv2.COLOR_BGR2GRAY)
    boxes, _ = hog.detectMultiScale(gray, winStride=(8, 8))
    return len(boxes) > 0

# Detect mask from full frame
def detect_mask_local(image_frame, model):
    image = cv2.resize(image_frame, (224, 224))
    image = image.astype("float32") / 255.0
    image = np.expand_dims(image, axis=0)

    prediction = model.predict(image)[0]
    label = "mask" if np.argmax(prediction) == 0 else "no-mask"
    return label

# Detect earmuff from full frame
def detect_earmuff_local(image_frame, model):
    image = cv2.resize(image_frame, (224, 224))
    image = image.astype("float32") / 255.0
    image = np.expand_dims(image, axis=0)

    prediction = model.predict(image)[0]
    label = "with_earmuff" if np.argmax(prediction) == 0 else "without_earmuff"
    return label

# Publish screenshot to MQTT
def publish_screenshot(image_frame):
    _, buffer = cv2.imencode('.jpg', image_frame)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    client.publish(REPORT_TOPIC, encoded_image)
    print("Published screenshot to topic:", REPORT_TOPIC)

# Publish PM alert to MQTT
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
        print("PM alert sent to:", PM_ALERT_TOPIC)
        last_pm_alert_time = current_time
    else:
        print("PM alert throttled to avoid spamming.")

# Main detection loop
def detection_loop():
    while True:
        if detect_mask or detect_headphones:
            image_path, image_frame = capture_image()
            print("Captured frame.")

            if not detect_person(image_frame):
                print("No person detected → skipping PPE checks")
                continue

            mask_result = detect_mask_local(image_frame, mask_model) if detect_mask else "No detection"
            headphone_result = detect_earmuff_local(image_frame, earmuff_model) if detect_headphones else "No detection"

            print("Mask Result:", mask_result)
            print("Headphone Result:", headphone_result)

            # Mark violations if any
            if mask_result == "no-mask":
                add_violation("no_mask")
            if headphone_result == "without_earmuff":
                add_violation("no_earmuff")

            if mask_result == "no-mask" or headphone_result == "without_earmuff":
                publish_screenshot(image_frame)
            if detect_mask and mask_result == "no-mask":
                prepare_and_publish_pm_alert(image_frame)
        
        time.sleep(1)

# MQTT setup
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe([
    (PM_STATUS_TOPIC, 0),
    (NOISE_STATUS_TOPIC, 0),
    (GET_PICTURE_TOPIC, 0),
    (GET_GRAPH_TOPIC,0)
])

print("MQTT client initialized. Waiting for sensor events...")

# Start detection loop in a separate thread
threading.Thread(target=detection_loop, daemon=True).start()
client.loop_forever()
