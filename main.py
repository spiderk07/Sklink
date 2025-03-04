from configs import Config
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
import re
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Client for Inline Search
Bot = Client(
    Config.BOT_SESSION_NAME,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User Client for Searching in Channels
User = Client(
    "user",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.USER_SESSION_STRING
)

# Start User client at the beginning
async def start_user_client():
    if not User.is_connected:
        try:
            await User.start()
            logger.info("User client started successfully.")
        except Exception as e:
            logger.error(f"Error starting User client: {e}")

# Function to replace Telegram links with a custom username
def replace_telegram_links(text):
    return re.sub(r'https?://t\.me/[^\s]+', 'https://t.me/skfilmbox', text)

# Function to delete a message after a delay
async def delete_schedule(bot, message, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_messages(chat_id=message.chat.id, message_ids=message.id)
    except Exception as e:
        logger.error(f"Error occurred while deleting message: {e}")

# Wrapper function to save a message for deletion after a specific time
async def save_dlt_message(bot, message, delete_after_seconds: int):
    await delete_schedule(bot, message, delete_after_seconds)

# Function to get IMDB movie suggestions
def get_imdb_suggestions(query):
    url = f"https://www.omdbapi.com/?s={query}&apikey={Config.IMDB_API_KEY}"
    response = requests.get(url).json()
    if response.get("Response") == "True":
        return [(movie["Title"], movie["imdbID"]) for movie in response.get("Search", [])]
    return []

# Handle '/start' command
@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, event: Message):
    await event.reply_photo(
        "https://telegra.ph/file/2b160d9765fe080c704d2.png",
        caption=Config.START_MSG.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔰 Donate us 🔰", url="https://p.paytm.me/xCTH/vo37hii9")],
            [InlineKeyboardButton("⚡️ LazyDeveloper ⚡️", url="https://t.me/LazyDeveloper")],
            [InlineKeyboardButton("🤖 Help", callback_data="Help_msg"),
             InlineKeyboardButton("🧑‍💻 About", callback_data="About_msg")]
        ])
    )

# Handle incoming messages and perform the inline search
@Bot.on_message(filters.incoming)
async def inline_search(bot, message: Message):
    if not message.text or message.text.strip() == '/start':
        return
    
    await start_user_client()  # Ensure User client is started
    query = message.text.strip()
    channels = Config.CHANNEL_IDS  # List of multiple channel IDs
    
    searching_msg = await message.reply_text("🔍 Searching for results, please wait...")
    
    found_results = []
    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query, limit=50):
                name = msg.text or msg.caption
                if name:
                    found_results.append(replace_telegram_links(name))

        await searching_msg.delete()
        
        if found_results:
            total_results = len(found_results)
            results_text = f"🔍 **Total Results Found: {total_results}**\n\n"
            page_result = found_results[0]
            results = f"🎬 **{page_result}**"

            # Pagination buttons
            buttons = []
            if total_results > 1:
                buttons.append(InlineKeyboardButton("Next ⏭", callback_data=f"page_2_{query}"))
            reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

            msg = await message.reply_text(
                text=results_text + results,
                reply_markup=reply_markup
            )
            await save_dlt_message(bot, msg, 300)  # Delete after 5 minutes
        else:
            imdb_suggestions = get_imdb_suggestions(query)
            buttons = []
            if imdb_suggestions:
                buttons.extend([
                    [InlineKeyboardButton(f"🎬 {title}", callback_data=f"imdb_{imdb_id}")]
                    for title, imdb_id in imdb_suggestions[:5]
                ])
            buttons.append([InlineKeyboardButton("📩 Request Admin", url="https://t.me/AdminContact")])
            await message.reply_text(
                "No exact results found. You can try these suggestions or request from admin:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except Exception as e:
        logger.error(f"Error occurred in search: {e}")
        await message.reply("An error occurred while processing your request. Please try again later.")

# Start the bot client
if __name__ == "__main__":
    Bot.run()
