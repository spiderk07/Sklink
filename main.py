from configs import Config
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import QueryIdInvalid
import asyncio
import re

# Bot Client for Inline Search
Bot = Client(
    Config.BOT_SESSION_NAME,  # Use positional argument for session_name
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User Client for Searching in Channel
User = Client(
    "user",  # Added a session name for the User client
    api_id=Config.API_ID,  # added api_id
    api_hash=Config.API_HASH,  # added api_hash
    session_string=Config.USER_SESSION_STRING  # added session_string
)

RESULTS_PER_PAGE = 1  # Number of results per page

# Function to replace Telegram links with your specific username
def replace_telegram_links(text):
    return re.sub(r'https?://t\.me/[^\s]+', 'https://t.me/skfilmbox', text)

# Function to delete a message after a delay
async def delete_schedule(bot, message, delay: int):
    await asyncio.sleep(delay)
    try:
        await bot.delete_messages(chat_id=message.chat.id, message_ids=message.id)
    except Exception as e:
        print(f"Error occurred while deleting message: {e}")

# Wrapper function to save a message for deletion after a specific time
async def save_dlt_message(bot, message, delete_after_seconds: int):
    await delete_schedule(bot, message, delete_after_seconds)

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

# Handle the '/help' command
@Bot.on_message(filters.private & filters.command("help"))
async def help_handler(_, event: Message):
    await event.reply_text(
        Config.ABOUT_HELP_TEXT.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Updates", url="https://t.me/LazyDeveloper"),
             InlineKeyboardButton("Support Group", url="https://t.me/LazyPrincessSupport"),
             InlineKeyboardButton("About", callback_data="About_msg")]
        ])
    )

# Handle incoming messages and perform the inline search
@Bot.on_message(filters.incoming)
async def inline_search(bot, message: Message):
    if message.text == '/start':
        return
    query = message.text
    channels = [Config.CHANNEL_ID]  # Can be a list of channel IDs

    found_results = []
    try:
        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query, limit=50):
                name = msg.text or msg.caption
                if name:
                    found_results.append(replace_telegram_links(name))

        if found_results:
            total_results = len(found_results)
            results_text = f"🔍 **Total Results Found: {total_results}**\n\n"
            start_idx = 0  # Start at the first result
            page_result = found_results[start_idx]
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
            await message.reply_text("No results found for your query.")
    except Exception as e:
        print(f"Error occurred in search: {e}")
        await message.reply("An error occurred while processing your request. Please try again later.")

# Handle pagination with callback queries (previous and next pages)
@Bot.on_callback_query(filters.regex(r"^page"))
async def page_navigation(bot, update: CallbackQuery):
    try:
        data = update.data.split("_")
        page_number = int(data[1])
        query = data[2]

        channels = [Config.CHANNEL_ID]  # Can be a list of channel IDs
        found_results = []

        for channel in channels:
            async for msg in User.search_messages(chat_id=channel, query=query, limit=50):
                name = msg.text or msg.caption
                if name:
                    found_results.append(replace_telegram_links(name))

        total_results = len(found_results)
        start_idx = (page_number - 1) * RESULTS_PER_PAGE
        if start_idx >= total_results:
            await update.answer("No more results available.", show_alert=True)
            return

        # Prepare the next page result
        page_result = found_results[start_idx]
        results = f"🎬 **{page_result}**"

        buttons = []
        if page_number > 1:
            buttons.append(InlineKeyboardButton("⏪ Previous", callback_data=f"page_{page_number - 1}_{query}"))
        if start_idx + RESULTS_PER_PAGE < total_results:
            buttons.append(InlineKeyboardButton("Next ⏭", callback_data=f"page_{page_number + 1}_{query}"))

        # Delete the current message
        await update.message.delete()

        # Send the new page results
        reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
        new_msg = await bot.send_message(
            chat_id=update.message.chat.id,
            text=results,
            reply_markup=reply_markup
        )

        # Schedule auto-deletion of the new message
        await save_dlt_message(bot, new_msg, 300)

    except Exception as e:
        print(f"Error occurred in page navigation: {e}")
        await update.answer("An error occurred while navigating. Please try again later.", show_alert=True)

# Start the bot clients
Bot.start()
User.start()
# Loop the clients till they disconnect
asyncio.get_event_loop().run_forever()

