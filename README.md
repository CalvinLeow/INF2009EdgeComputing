# Smart Environmental Monitoring System by Group 10
Smart Environmental Monitoring System for Construction Sites is an AI-powered safety enforcement system that uses real-time image recognition and environmental monitoring to ensure compliance with workplace safety regulations. 

## MQTT
> The team implemented the Message Queuing Telemetry Transport (MQTT) protocol to facilitate communication both among devices and between devices and the Telegram bot. This was achieved using a publish-subscribe model, with a carefully organized set of topics to ensure seamless and efficient data exchange across all system components.

### FileName.py

Words Here

### Tested/Tried (Additional Notes):

Words Here

## Telegram Bot
> The team chose a Telegram bot for its practicality, ensuring site workers receive alerts directly on their phones. Using BotFather and the Telegram Bot API, a secure, user-friendly bot was developed to send commands via MQTT and receive text, images, and graphs for alerts. It seamlessly integrates with Telegram Groups and facilitates communication between workers and managers.

### FileName.py

Words Here

### Tested/Tried (Additional Notes):

Words Here

## Particulate Sensor
> The system uses a particulate matter sensor to measure PM2.5 levels in real-time. The data processed checks against safety thresholds (55 µg/m³), and logs readings with timestamps. High PM2.5 triggers MQTT alerts and Telegram notifications, while historical data is stored for ML analysis and visualization.

### FileName.py

Words Here

### Tested/Tried (Additional Notes):

Words Here

## Sound Sensor
> The system utilizes the webcam's microphone to measure the decibel level in real time. The processed data is compared against a safety threshold of 50 dB and logged with timestamps, including the change from the previous value. If a high decibel level is detected, an MQTT alert and a Telegram notification are triggered. Additionally, historical data is stored for machine learning analysis and visualization.

### mic_sensor_new.py

reads the noice, which is recieved by the microphone and calculated it to decibel
it stores the entry with a timestamp and the difference to the last value in a .csv file localy
when it measures a decibel higher than 50 dB, it triggers an MQTT message with the input "HIGH" to the detection_webcam.py code
When the .csv file reaches 1000 entries, it deletes the first 100 entries and sends an MQTT message to the mic_sensor_ml.py to retrain the ML model

### mic_sensor_ml.py

When it recieves the retrain message from the mic_sensor_new.py code, it retrain the model based on the readings in the .csv file
After that it uses the model to predict the next time when the decibel will hit the 50 dB mark. When it is in the next 2 hours, it will send an MQTT message to the telegram_bot.py code with the predicted time. If it is longer than 2 hours, it will ignore it.

### mic_sensor_handler.py

The code listens to the telegram_bot.py code. When it recieves a MQTT message from the telegram_bot.py code to provide the current reading or the decibel graph, it will look for the latest entry in the .csv file or generates a decibel graph out of the readings and send it to the telegram_bot.py code.

### Tested/Tried (Additional Notes):

Words Here

## ML Predictions
> The system uses two lightweight computer vision models to detect ear muffs and face masks. When high noise levels or PM2.5 concentrations are detected, it captures an image and checks for PPE compliance. If non-compliance is found, a violation alert with the image is sent via MQTT to a Telegram bot for instant notification.

### FileName.py

Words Here

### Tested/Tried (Additional Notes):

Words Here

## Camera Detection
> The system uses two lightweight computer vision models to detect ear muffs and face masks. When high noise levels or PM2.5 concentrations are detected, it captures an image and checks for PPE compliance. If non-compliance is found, a violation alert with the image is sent via MQTT to a Telegram bot for instant notification.

### FileName.py

Words Here

### Tested/Tried (Additional Notes):

Words Here



