import asyncio
import logging
from datetime import datetime, timezone

from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, PeerIdInvalid
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

# Assuming Config is in a separate file called config.py
from config import Config  # Import the Config class

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Bot Client for Inline Search
Bot = Client(
    name=Config.BOT_SESSION_NAME,  # Use keyword argument for session_name
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
)

# User Client for Searching in Channel.
User = Client(
    name="user",  # Added a session name for the User client, use keyword argument
    api_id=Config.API_ID,  # added api_id
    api_hash=Config.API_HASH,  # added api_hash
    session_string=Config.USER_SESSION_STRING,  # added session_string
)

# Dictionary to store search results and current index for each user
search_results = {}


@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, event: Message):
    """Handles the /start command."""
    await event.reply_photo(
        "https://telegra.ph/file/2b160d9765fe080c704d2.png",
        caption=Config.START_MSG.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔺 Donate us 🔺", url="https://p.paytm.me/xCTH/vo37hii9")],
                [InlineKeyboardButton("⚡️ LazyDeveloper ⚡️", url="https://t.me/LazyDeveloper")],
                [
                    InlineKeyboardButton("🤒Help", callback_data="Help_msg"),
                    InlineKeyboardButton("🦋About", callback_data="About_msg"),
                ],
            ]
        ),
    )


@Bot.on_message(filters.private & filters.command("help"))
async def help_handler(_, event: Message):
    """Handles the /help command."""
    await event.reply_text(
        Config.ABOUT_HELP_TEXT.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Updates", url="https://t.me/LazyDeveloper"),
                    InlineKeyboardButton("Support Group", url="https://t.me/LazyPrincessSupport"),
                    InlineKeyboardButton("About", callback_data="About_msg"),
                ]
            ]
        ),
    )


@Bot.on_message(filters.incoming)
async def inline_handlers(_, event: Message):
    """Handles incoming messages and performs inline search."""
    if event.text == "/start":
        return

    user_id = event.from_user.id
    search_results[user_id] = {"results": [], "index": 0}  # Initialize

    try:
        results = []
        async for message in User.search_messages(
            chat_id=Config.CHANNEL_ID, limit=50, query=event.text
        ):
            if message.text:
                f_text = message.text
                if "|||" in message.text:
                    f_text = message.text.split("|||", 1)[0]

                try:
                    title = f_text.split("\n", 1)[0]
                    description = f_text.split("\n", 2)[-1]
                    result_text = (
                        f"**🎞 ➠ {title}\n\n {description} \n\n"
                        "▰▱▰▱▰▱▰▱▰▱▰▱▰▱\n"
                        "Link Will Auto Delete In 35Sec...⏰\n"
                        "▰▱▰▱▰▱▰▱▰▱▰▱▰▱\n\n**"
                    )
                    results.append(result_text)
                except IndexError as e:
                    logger.warning(f"IndexError while processing message: {e}")

        search_results[user_id]["results"] = results
        search_results[user_id]["index"] = 0

        if results:
            await display_result(event.chat.id, user_id)
        else:
            await event.reply_text(
                "No results found. Please check your search query."
            )

    except Exception as e:
        logger.exception(f"Error during search: {e}")


async def display_result(chat_id, user_id):
    """Displays a single search result with a 'Next' button and auto-deletion."""
    if user_id not in search_results or not search_results[user_id]["results"]:
        await Bot.send_message(chat_id, "No results found.")
        return

    results = search_results[user_id]["results"]
    index = search_results[user_id]["index"]

    if 0 <= index < len(results):
        result_text = results[index]
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Next ➡️", callback_data=f"next_{user_id}")]]
        )
        message = await Bot.send_message(chat_id, result_text, reply_markup=keyboard)

        # Schedule message deletion after 5 minutes (300 seconds)
        await asyncio.sleep(300)
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")
    else:
        await Bot.send_message(chat_id, "No more results.")


@Bot.on_callback_query(filters.regex("^next_"))
async def next_result_handler(_, query: CallbackQuery):
    """Handles the 'Next' button click."""
    user_id = int(query.data.split("_")[1])
    chat_id = query.message.chat.id

    if user_id not in search_results:
        await query.answer("Search session expired.")
        return

    search_results[user_id]["index"] += 1
    index = search_results[user_id]["index"]
    results = search_results[user_id]["results"]

    try:
        await query.message.delete()  # Delete the previous message
        await Bot.send_sticker(chat_id, sticker="CAACAgUAAxkBAAEZxWZlOTZTb9zlQzcx1IBYhgQfRAa1AQACXwEAAp-f5VMtLdxjnluVti8E")
        if 0 <= index < len(results):
          await asyncio.sleep(2)
          await display_result(chat_id, user_id)

        else:
          await asyncio.sleep(2)
          await Bot.send_message(chat_id, "No more results.")

    except Exception as e:
        logger.exception(f"Error handling next button: {e}")

@Bot.on_callback_query()
async def button(bot, cmd: CallbackQuery):
    """Handles callback queries from inline keyboard buttons."""
    cb_data = cmd.data
    try:
        if "About_msg" in cb_data:
            await cmd.message.edit(
                text=Config.ABOUT_BOT_TEXT,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Updates Channel", url="https://t.me/LazyDeveloper"
                            )
                        ],
                        [
                            InlineKeyboardButton("Connect Admin", url="https://t.me/LazyDeveloper"),
                            InlineKeyboardButton("🏠Home", callback_data="gohome"),
                        ],
                    ]
                ),
                parse_mode="html",
            )
        elif "Help_msg" in cb_data:
            await cmd.message.edit(
                text=Config.ABOUT_HELP_TEXT,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("Help", callback_data="Help_msg"),
                            InlineKeyboardButton(
                                "Updates Channel", url="https://t.me/LazyDeveloper"
                            ),
                        ],
                        [
                            InlineKeyboardButton("Connect Admin", url="https://t.me/LazyDeveloper"),
                            InlineKeyboardButton("🏠Home", callback_data="gohome"),
                        ],
                    ]
                ),
                parse_mode="html",
            )
        elif "gohome" in cb_data:
            await cmd.message.edit(
                text=Config.START_MSG.format(cmd.from_user.mention),
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("Help", callback_data="Help_msg"),
                            InlineKeyboardButton("About", callback_data="About_msg"),
                        ],
                        [
                            InlineKeyboardButton(
                                "Support Channel", url="https://t.me/LazyPrincessSupport"
                            ),
                        ],
                    ]
                ),
                parse_mode="html",
            )
    except Exception as e:
        logger.exception(f"Error handling callback query: {e}")


async def main():
    """Starts and stops the clients."""
    try:
        await Bot.start()
        await User.start()
        logger.info("Clients started successfully.")
        await idle()  # Keep the clients running until Ctrl+C is pressed
    except Exception as e:
        logger.critical(f"Failed to start clients: {e}")
    finally:
        await Bot.stop()
        await User.stop()
        logger.info("Clients stopped.")


if __name__ == "__main__":
    asyncio.run(main())
