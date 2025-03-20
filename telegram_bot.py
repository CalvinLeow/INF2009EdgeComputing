import asyncio
import logging
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import paho.mqtt.client as mqtt  # MQTT library for integration

# # Enable logging
# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO
# )

# logger = logging.getLogger(__name__)

# Define the MQTT broker settings
MQTT_BROKER = "localhost"  # Example broker, change to your MQTT broker
MQTT_PORT = 1883
MQTT_TOPIC = "test/topic"  # Replace with your topic

# Define the Telegram Bot token
TELEGRAM_BOT_TOKEN = "7268963773:AAFSMbtVJGDl19mxgQXNvayK5wXyGCqp72Q"
ALLOWED_CHAT_IDS = {2021714746, -4746695132, -4718771410}  # Set of allowed chat IDs

# Define the MQTT topics and messages in a dictionary
MQTT_BUTTONS = {
    "mqtt_button_1": {"topic": "topic/getPicture", "message": "getPicture"},
    "mqtt_button_2": {"topic": "topic/getDust", "message": "getDust"},
    "mqtt_button_3": {"topic": "topic/getSound", "message": "getSound"},
    "mqtt_button_4": {"topic": "topic/getGraph/dust", "message": "getGraphDust"},
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

# Define a few command handlers. These usually take the two arguments update and context.

# Function to generate the main keyboard
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Take Picture", callback_data="mqtt_button_1")],
        [InlineKeyboardButton("🌫 Current Dust Reading", callback_data="mqtt_button_2")],
        [InlineKeyboardButton("🔊 Current Sound Reading", callback_data="mqtt_button_3")],
        [InlineKeyboardButton("Placeholder Button", callback_data="button_1")],
        [InlineKeyboardButton("📈 Graphs", callback_data="button_2")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued and store the chat_id."""
    user = update.effective_user
    chat_id = update.message.chat.id

    # Check if the chat_id is in the allowed list
    if chat_id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("You are not authorized to use this bot.")
        return  # Exit the function early if not authorized
    
    user_chat_ids[chat_id] = chat_id  # Store the chat_id for the user
    print(f"{chat_id} added. List of IDs: {user_chat_ids}")


    await update.message.reply_html(
        rf"{user.mention_html()} has started the Smart Environment Monitoring System! The bot will now send messages to this chat.",
        reply_markup = get_keyboard()
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

        # Optionally, update with another set of buttons based on the action
        elif button_id == "button_2":
            new_keyboard = [
                [InlineKeyboardButton("🌫📈 Get Dust Graph", callback_data="mqtt_button_4")],
                [InlineKeyboardButton("🔊📈 Get Sound Graph", callback_data="mqtt_button_5")],
                [InlineKeyboardButton("📷📈 Get Camera Violations Graph", callback_data="mqtt_button_6")],
                [InlineKeyboardButton("<< Back", callback_data="back")],
            ]
            await query.edit_message_text(
                text="You pressed a custom button. Here are your next options.",
                reply_markup=InlineKeyboardMarkup(new_keyboard)
            )
        # You can define more cases for custom actions based on the button pressed

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
    # logger.info(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    """Called when a message is received from the MQTT broker."""
    # Handle incoming MQTT message and send it to the user
    message = msg.payload.decode()
    topic = msg.topic
    # logger.info(f"Received message: {message} on topic: {topic}.")
    print(f"Received message: {message} on topic: {topic}.")

    # Send the MQTT message to all users who have started the bot
    for chat_id in user_chat_ids.values():
        loop.call_soon_threadsafe(asyncio.create_task, send_telegram_message(chat_id, message))

async def send_telegram_message(chat_id: int, message: str) -> None:
    """Send a message to the specified Telegram chat."""
    await application.bot.send_message(chat_id=chat_id, text=message)

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

    # Run the Telegram bot in a separate thread or process
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
