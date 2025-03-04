from configs import Config
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
import re
import logging
from imdb import Cinemagoer

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

ia = Cinemagoer()

async def search_imdb(query):
    try:
        int(query)
        movie = ia.get_movie(query)
        return movie["title"]
    except Exception as e:
        logger.error(f"Error searching IMDb: {e}")
        movies = ia.search_movie(query, results=10)
        list = []
        for movie in movies:
            title = movie["title"]
            try:
                year = f" - {movie['year']}"
            except:
                year = ""
            list.append({"title": title, "year": year, "id": movie.movieID})
        return list

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

# Handle '/start' command
@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, message: Message):
    mention = message.from_user.mention
    await message.reply_photo(
        "https://graph.org/file/9e75acb615bf3b613a811-b06ba8cdabe4216f6a.jpg",
        caption=Config.START_MSG.format(mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔰 Donate us 🔰", url="https://razorpay.me/@skfilmbox")],
            [InlineKeyboardButton("⚡️ Skfilmbox ⚡️", url="https://t.me/skfilmbox")],
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
    
    mention = message.from_user.mention
    searching_msg = await message.reply_text(f"🔍 Searching for {query}... {mention}")
    
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
            results_text = f"★ **Pᴏᴡᴇʀᴇᴅ ʙʏ : @SkFilmBox \n\n🔎 Total Results:: {total_results}**\n\n"
            page_result = found_results[0]
            results = f"🎬 **{page_result}**"

            # Pagination buttons
            buttons = []
            if total_results > 1:
                buttons.append(InlineKeyboardButton("Next ⏭", callback_data=f"page_2_{query}"))
            reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

            msg = await message.reply_text(
                text=results_text + results + f"\n\n{mention}",
                reply_markup=reply_markup
            )
            await save_dlt_message(bot, msg, 300)  # Delete after 5 minutes
        else:
            movie_suggestions = await search_imdb(query)
            if movie_suggestions:
                # Fallback if no results found
                buttons = [[InlineKeyboardButton(movie["title"], callback_data=f"recheck_{movie['id']}")] for movie in movie_suggestions]
                buttons.append([InlineKeyboardButton("📩 Request Admin", url="https://t.me/skAdminrobot")])
                
                msg = await message.reply_photo(
                    photo="https://graph.org/file/9e75acb615bf3b613a811-b06ba8cdabe4216f6a.jpg",
                    caption=f"<b><i>Sorry, no results found for your query 😕.\nDid you mean any of these?</i></b>\n\n{mention}", 
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                await save_dlt_message(bot, msg, 300)  # Delete after 5 minutes
            else:
                buttons = [[InlineKeyboardButton("📩 Request Admin", url="https://t.me/skAdminrobot")]]
                await message.reply_text(
                    f"No results found for your query and no suggestions available.\n\n{mention}",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
    except Exception as e:
        logger.error(f"Error occurred in search: {e}")
        await searching_msg.delete()
        await message.reply(f"Please Follow WhatsApp Channel https://whatsapp.com/channel/0029Va69Ts2C6ZvmEWsHNo3c. {mention}")

# Handle pagination for search results
@Bot.on_callback_query(filters.regex(r"^page_(\d+)_(.+)"))
async def paginate_results(bot, query: CallbackQuery):
    page_number = int(query.matches[0].group(1))
    search_query = query.matches[0].group(2)
    channels = Config.CHANNEL_IDS  # List of multiple channel IDs

    await start_user_client()  # Ensure User client is started

    found_results = []
    try:
        # Show a sticker before displaying the next results
        sticker_message = await query.message.reply_sticker(sticker="CAACAgIAAxkBAAKf0WfHKVH5auqyUzh649nVPJVm29IGAAJxCAAChJRBSW9oCRqmu85zNgQ")
        await asyncio.sleep(2)
        await sticker_message.delete()
        
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=search_query, limit=50):
                name = msg.text or msg.caption
                if name:
                    found_results.append(replace_telegram_links(name))

        total_results = len(found_results)
        start_index = (page_number - 1) * 1
        end_index = start_index + 1

        if start_index < total_results:
            page_result = found_results[start_index:end_index]
            results_text = f"★ **Pᴏᴡᴇʀᴇᴅ ʙʏ : @SkFilmBox \n\n🔎 Total Results: {total_results}**\n\n"
            results = f"🎬 **{page_result[0]}**"

            # Pagination buttons
            buttons = []
            if end_index < total_results:
                buttons.append(InlineKeyboardButton("Next ⏭", callback_data=f"page_{page_number + 1}_{search_query}"))
            if page_number > 1:
                buttons.append(InlineKeyboardButton("⏮ Previous", callback_data=f"page_{page_number - 1}_{search_query}"))
            reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

            await query.message.edit_text(
                text=results_text + results + f"\n\n{query.from_user.mention}",
                reply_markup=reply_markup
            )
        else:
            await query.answer("No more results available.")
    except Exception as e:
        logger.error(f"Error occurred in pagination: {e}")
        await query.message.reply(f"Please Follow WhatsApp Channel https://whatsapp.com/channel/0029Va69Ts2C6ZvmEWsHNo3c. {query.from_user.mention}")

# Handle movie recheck from IMDb suggestions
@Bot.on_callback_query(filters.regex(r"^recheck_(\d+)"))
async def recheck_movie(bot, query: CallbackQuery):
    movie_id = query.matches[0].group(1)
    movie = ia.get_movie(movie_id)
    title = movie["title"]

    # Show a sticker before displaying the results
    sticker_message = await query.message.reply_sticker(sticker="CAACAgIAAxkBAAKf1GfHKZMWJQGWXtjitWHKu_MSEEjbAAI8TAACBcnQS1AJylV4pVHqNgQ")
    await asyncio.sleep(2)
    await sticker_message.delete()

    # Perform the search again with the movie title
    await start_user_client()  # Ensure User client is started
    channels = Config.CHANNEL_IDS  # List of multiple channel IDs

    found_results = []
    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=title, limit=50):
                name = msg.text or msg.caption
                if name:
                    found_results.append(replace_telegram_links(name))

        if found_results:
            total_results = len(found_results)
            results_text = f"🔍 **Total Results Found: {total_results}**\n\n"
            page_result = found_results[0]
            results = f"🎬 **{page_result}**"

            # Pagination buttons
            buttons = []
            if total_results > 1:
                buttons.append(InlineKeyboardButton("Next ⏭", callback_data=f"page_2_{title}"))
            reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

            await query.message.edit_text(
                text=results_text + results + f"\n\n{query.from_user.mention}",
                reply_markup=reply_markup
            )
        else:
            buttons = [[InlineKeyboardButton("📩 Request Admin", url="https://t.me/skAdminrobot")]]
            await query.message.edit_text(
                f"No results found for your query.\n\n{query.from_user.mention}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except Exception as e:
        logger.error(f"Error occurred in recheck: {e}")
        await query.message.reply(f"Please Follow WhatsApp Channel https://whatsapp.com/channel/0029Va69Ts2C6ZvmEWsHNo3c. {query.from_user.mention}")

# Start the bot client
if __name__ == "__main__":
    Bot.run()
