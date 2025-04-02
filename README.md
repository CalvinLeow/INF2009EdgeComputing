# Smart Environmental Monitoring System by Group 10
Smart Environmental Monitoring System for Construction Sites is an AI-powered safety enforcement system that uses real-time image recognition and environmental monitoring to ensure compliance with workplace safety regulations. 

## MQTT
> The team implemented the Message Queuing Telemetry Transport (MQTT) protocol to facilitate communication both among devices and between devices and the Telegram bot. This was achieved using a publish-subscribe model, with a carefully organized set of topics to ensure seamless and efficient data exchange across all system components.

### telegram_bot.py

MQTT functionality was inplace in all the edge devices - but a central portion of the MQTT code is stored in the Telegram bot python file. Firstly, the Telegram bot functions as a "hub" where most of the edge devices communicate to the end user. The list of topics and callback functionalities with the code was designed to be easily extendable and scalable, utilising dictionaries, handlers and appropriate call back functions to enable MQTT communications to include things like graphs.

The team chose to use MQTT because it was simple, efficient and its familiarity and ease of use.

### Tested/Tried (Additional Notes):

The team tested MQTT communication for reliability, latency, scalability, and data handling by simulating multiple edge devices, monitoring message delivery efficiency, and ensuring proper data formatting and parsing.

## Telegram Bot
> The team chose a Telegram bot for its practicality, ensuring site workers receive alerts directly on their phones. Using BotFather and the Telegram Bot API, a secure, user-friendly bot was developed to send commands via MQTT and receive text, images, and graphs for alerts. It seamlessly integrates with Telegram Groups and facilitates communication between workers and managers.

### telegram_bot.py

The Telegram bot was built using Telegram's BotFather and official API. The bot is integrated to support the MQTT architecture, containing easily extendable and scalable buttons and UI as well as efficient and adaptable handlers and callback functions to support all required data types to be sent to the user. It handles all the on_connect and on_message interactions to ensure seamless and intuitive operation of the system. It also contains authentication and security measures written to ensure only authorised users can access the bot, this was done by having a whitelist that prevents unauthorised users from communicating with the bot entirely. Similarly, the user or group's ID is also stored dynamically to know who and where to send the output of edge devices to.

### Tested/Tried (Additional Notes):

The team considered developing a web application, but decided not to as it would be unnecessarily complicated and would not necessarily be better than a simple and intuitive Telegram bot. The team felt that a bot that can be easily accessible by phone, and can be used individually or as a group providing a realistic and appropriate use case scenario to support our end users. This is because construction work is frequently on the move, and a phone notification alert would be an acceptable level of effort required for busy workers to still fully utilise the system. The functinality of having the bot in a group chat is also an essential reason for choosing to use a Telegram bot, as workers and managers will have a common place to receive information, manage the bot, and discuss their work. They will be able to continue working the way they have used to - only this time with a beneficial add-on that does not distract from their jobs.

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



