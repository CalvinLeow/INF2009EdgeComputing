import asyncio
import logging
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import paho.mqtt.client as mqtt  # MQTT library for integration
import base64
from io import BytesIO
import json

# # Enable logging
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO
# )

# logger = logging.getLogger(__name__)

# Define the MQTT broker settings
MQTT_BROKER = "localhost"  # Example broker, change to your MQTT broker
MQTT_PORT = 1883
# MQTT_TOPIC = "test/topic"  # Replace with your topic

# Define the Telegram Bot token
TELEGRAM_BOT_TOKEN = "7268963773:AAFSMbtVJGDl19mxgQXNvayK5wXyGCqp72Q"
ALLOWED_CHAT_IDS = {2021714746, -4746695132, -4718771410, 5387486591,40684146}  # Set of allowed chat IDs

# Define the MQTT topics and messages in a dictionary
MQTT_BUTTONS = {
    "mqtt_button_1": {"topic": "topic/getPicture", "message": "getPicture"},
    "mqtt_button_2": {"topic": "topic/getPM", "message": "getPM"},
    "mqtt_button_3": {"topic": "topic/getSound", "message": "getSound"},
    "mqtt_button_4": {"topic": "topic/getGraph/pm", "message": "getGraphPM"},
    "mqtt_button_5": {"topic": "topic/getGraph/sound", "message": "getGraphSound"},
    "mqtt_button_6": {"topic": "topic/getGraph/camera", "message": "getGraphCamera"},
}

# Define non-MQTT buttons and their actions
NON_MQTT_BUTTONS = {
    "button_1": "You pressed 'Next Button 1'. Performing some action.",
    "button_2": "You pressed 'Next Button 2'. Performing another action.",
}

# Set up MQTT client
client = mqtt.Client()

# Store the chat_id dynamically for each user who starts the bot
user_chat_ids = {}

# Function to generate the main keyboard
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Take Picture", callback_data="mqtt_button_1")],
        [InlineKeyboardButton("Current PM Reading", callback_data="mqtt_button_2")],
        [InlineKeyboardButton("Current Sound Reading", callback_data="mqtt_button_3")],
        [InlineKeyboardButton("Placeholder Button", callback_data="button_1")],
        [InlineKeyboardButton("Graphs", callback_data="button_2")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued and store the chat_id."""
    user = update.effective_user
    chat_id = update.message.chat.id

    # Check if the chat_id is in the allowed list
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    user_chat_ids[chat_id] = chat_id  # Store the chat_id for the user
    print(f"{chat_id} added. List of IDs: {user_chat_ids}")

    await update.message.reply_html(
        rf"{user.mention_html()} has started the Smart Environment Monitoring System! The bot will now send messages to this chat.",
        reply_markup=get_keyboard()
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses and publish MQTT messages or perform other actions."""
    query = update.callback_query
    await query.answer()

    button_id = query.data

    # If the button is an MQTT-related button
    if button_id in MQTT_BUTTONS:
        mqtt_info = MQTT_BUTTONS[button_id]
        client.publish(mqtt_info["topic"], mqtt_info["message"])
        await query.message.reply_text(f"Published '{mqtt_info['message']}' to '{mqtt_info['topic']}'")

    # If the button is a non-MQTT button (custom action)
    elif button_id in NON_MQTT_BUTTONS:
        
        if button_id == "button_1":
            action_message = NON_MQTT_BUTTONS[button_id]
            await query.message.reply_text(action_message)
            
        elif button_id == "button_2":
            new_keyboard = [
                [InlineKeyboardButton("Get PM Graph", callback_data="mqtt_button_4")],
                [InlineKeyboardButton("Get Sound Graph", callback_data="mqtt_button_5")],
                [InlineKeyboardButton("Get Camera Violations Graph", callback_data="mqtt_button_6")],
                [InlineKeyboardButton("<< Back", callback_data="back")],
            ]
            await query.edit_message_text(
                text="You pressed a custom button. Here are your next options.",
                reply_markup=InlineKeyboardMarkup(new_keyboard)
            )

    # If Back button is pressed, return to main menu
    elif button_id == "back":
        await query.edit_message_text(
            text="Welcome to the Smart Environment Monitoring System! The bot will now send messages to this chat.",
            reply_markup=get_keyboard()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Hello! I am a Telegram Bot designed to help you publish and subscribe to your edge device. I also serve as the User Interface for viewing analytics conducted on the edge!")

# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Echo the user message."""
#     await update.message.reply_text(update.message.text)

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    """Called when the MQTT client connects to the broker."""
    client.subscribe("sensor/picture")
    client.subscribe("sensor/pm_reading")
    client.subscribe("sensor/pm_graph")
    client.subscribe("sensor/PMAlertMessage")
    client.subscribe("sensor/SoundAlert")
    client.subscribe("sensor/pm_prediction")
    client.subscribe("sensor/violation_graph")
    client.subscribe("sensor/sound_reading")
    client.subscribe("sensor/sound_graph")
    client.subscribe("sensor/SoundAlert")

def on_message(client, userdata, msg):
    """Called when a message is received from the MQTT broker."""
    topic = msg.topic
    print(f"Received message on topic: {topic}.")

    # Send the MQTT message to all users who have started the bot
    for chat_id in user_chat_ids.values():
        loop.call_soon_threadsafe(asyncio.create_task, handle_mqtt_message(chat_id, topic, msg.payload))

async def handle_mqtt_message(chat_id, topic, message):
    try:
        if topic == "sensor/picture":
            decoded_image = base64.b64decode(message)
            image_file = BytesIO(decoded_image)
            await application.bot.send_photo(chat_id=chat_id, photo=image_file)
        elif topic == "sensor/PMAlertMessage":
            payload = json.loads(message.decode())
            decoded_image = base64.b64decode(payload["image"])
            image_file = BytesIO(decoded_image)
            caption = f"{payload['message']}\nPM2.5: {payload['pm_reading']}"
            await application.bot.send_photo(chat_id=chat_id, photo=image_file, caption=caption)
        elif topic == "sensor/pm_reading":
            parsed = json.loads(message.decode())
            formatted = "\n".join([f"{r['timestamp']}: {r['pm2_5']} ug/m3 ({r['status']})" for r in parsed])
            await application.bot.send_message(chat_id=chat_id, text=f"Latest PM Readings:\n{formatted}")
        elif topic == "sensor/sound_reading":
            parsed = json.loads(message.decode())
            formatted = f"Timestamp: {parsed['timestamp']}\nSound Level: {parsed['sound_level']} dB"
            await application.bot.send_message(chat_id=chat_id, text=f"Latest PM Readings:\n{formatted}")
        elif topic == "sensor/SoundAlert":
            await application.bot.send_message(chat_id=chat_id, text=message.decode())
        elif topic == "sensor/pm_graph":
            image_file = BytesIO(message)
            await application.bot.send_photo(chat_id=chat_id, photo=image_file, caption="PM2.5 Graph")
        elif topic == "sensor/sound_graph":
            image_file = BytesIO(message)
            await application.bot.send_photo(chat_id=chat_id, photo=image_file, caption="PM2.5 Graph")
        elif topic == "sensor/pm_prediction":
            predicted_value = message.decode()
            await application.bot.send_message(
                chat_id=chat_id,
                text=f"Predicted PM2.5 value in 5 hours: {predicted_value} µg/m³"
            )
        elif topic == "sensor/violation_graph":
            image_file = BytesIO(message)
            await application.bot.send_photo(chat_id=chat_id, photo=image_file, caption="Violation Graph")

        else:
            await application.bot.send_message(chat_id=chat_id, text=message.decode())
    except Exception as e:
        await application.bot.send_message(chat_id=chat_id, text=f"Error handling message: {str(e)}")

def main() -> None:
    """Start the bot and MQTT client."""
    
    # Set up the Application (Telegram bot)
    global application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # # Add message handler for echoing
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Add handler for inline button presses
    application.add_handler(CallbackQueryHandler(button_callback))

    # Set up MQTT client
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Start the MQTT client loop in the background
    client.loop_start()

    # Get the current event loop
    global loop
    loop = asyncio.get_event_loop()
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
