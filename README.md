mic_sensor_new.py
reads the noice, which is recieved by the microphone and calculated it to decibel
it stores the entry with a timestamp and the difference to the last value in a .csv file localy
when it measures a decibel higher than 50 dB, it triggers an MQTT message with the input "HIGH" to the detection_webcam.py code
When the .csv file reaches 1000 entries, it deletes the first 100 entries and sends an MQTT message to the mic_sensor_ml.py to retrain the ML model

mic_sensor_ml.py
When it recieves the retrain message from the mic_sensor_new.py code, it retrain the model based on the readings in the .csv file
After that it uses the model to predict the next time when the decibel will hit the 50 dB mark. When it is in the next 2 hours, it will send an MQTT message to the telegram_bot.py code with the predicted time. If it is longer than 2 hours, it will ignore it.

mic_sensor_handler.py
The code listens to the telegram_bot.py code. When it recieves a MQTT message from the telegram_bot.py code to provide the current reading or the decibel graph, it will look for the latest entry in the .csv file or generates a decibel graph out of the readings and send it to the telegram_bot.py code.
