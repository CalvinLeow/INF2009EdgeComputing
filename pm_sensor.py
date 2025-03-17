import serial
import struct
import paho.mqtt.client as mqtt
import time

# Serial connection details
SERIAL_PORT = "/dev/serial0"  # Use "/dev/ttyS0" if needed
BAUD_RATE = 9600
PM_THRESHOLD = 0  #for testing purpose, actual dangerous level is above 55

# MQTT details
MQTT_BROKER = "localhost"  # Change if using an external broker
MQTT_PORT = 1883
PM_STATUS_TOPIC = "sensor/pm_status"

# Setup MQTT client
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
    print("Listening for PMS5003 sensor data... Press Ctrl+C to stop.")

    while True:
        header = ser.read(2)
        if header == b'\x42\x4D':  # Valid header detected
            frame = ser.read(30)
            if len(frame) != 30:
                print("Error: Incomplete frame received. Skipping...")
                continue

            try:
                data = struct.unpack(">HHHHHHHHHHHHHH", frame[:28])  # Unpack 28 bytes
                pm2_5_atm = data[4]  # Extract PM2.5 (ATM)

                print("PM2.5 (ATM):", pm2_5_atm, "ug/m3")

                # Determine status based on PM2.5 threshold
                status = "HIGH" if pm2_5_atm > PM_THRESHOLD else "LOW"
                
                # Publish PM2.5 status
                client.publish(PM_STATUS_TOPIC, status)
                print(f"Published {status} to {PM_STATUS_TOPIC}")

            except struct.error:
                print("Error: Unable to unpack data. Skipping frame...")
                continue

        time.sleep(2)  # Adjust polling interval

except KeyboardInterrupt:
    print("Exiting...")
    ser.close()
