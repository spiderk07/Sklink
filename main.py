from configs import Config
from pyrogram import Client, filters, idle
from pyrogram.errors import QueryIdInvalid
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Sticker
from LazyDeveloper.forcesub import ForceSub
import asyncio
import time  # Import the time module

# Bot Client for Inline Search
Bot = Client(
    session_name=Config.BOT_SESSION_NAME,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User Client for Searching in Channel.
User = Client(
    name="user",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.USER_SESSION_STRING
)

search_results = {}  # Store search results for each user
current_index = {}  # Store the current index for each user

@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, event: Message):
    await event.reply_photo("https://telegra.ph/file/2b160d9765fe080c704d2.png",
                                caption=Config.START_MSG.format(event.from_user.mention),
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("ðŸ”º Donate us ðŸ”º", url="https://p.paytm.me/xCTH/vo37hii9")],
                                    [InlineKeyboardButton("âš¡ï¸ LazyDeveloper âš¡ï¸", url="https://t.me/LazyDeveloper")],
                                    [InlineKeyboardButton("ðŸ¤’Help", callback_data="Help_msg"),
                                    InlineKeyboardButton("ðŸ¦‹About", callback_data="About_msg")]]))

@Bot.on_message(filters.private & filters.command("help"))
async def help_handler(_, event: Message):

    await event.reply_text(Config.ABOUT_HELP_TEXT.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Updates", url="https://t.me/LazyDeveloper"),
             InlineKeyboardButton("Support Group", url="https://t.me/LazyPrincessSupport"),
             InlineKeyboardButton("About", callback_data="About_msg")]
        ])
    )

@Bot.on_message(filters.incoming)
async def inline_handlers(_, event: Message):
    if event.text == '/start':
        return

    user_id = event.from_user.id
    search_results[user_id] = []  # Initialize search results for the user
    current_index[user_id] = 0  # Initialize current index for the user

    async for message in User.search_messages(chat_id=Config.CHANNEL_ID, limit=50, query=event.text):
        search_results[user_id].append(message)

    if not search_results[user_id]:
        await event.reply_text("No results found.")
        return

    await display_message(event, user_id)

async def display_message(event: Message, user_id: int):
    index = current_index[user_id]
    results = search_results[user_id]

    if index >= len(results):
        await event.reply_text("No more results.")
        return

    message = results[index]

    if message.text:
        f_text = message.text
        if "|||" in message.text:
            f_text = message.text.split("|||", 1)[0]

        text = f'**ðŸŽž âž  ' + '' + f_text.split("\n", 1)[0] + '' + '\n\n ' + '' + f_text.split("\n", 2)[-1] + ' \n\nLink Will Auto Delete In 5Min...â°\nâ–°â–±â–°â–±â–°â–±â–°â–±â–°â–±â–°â–±â–°â–±\n\n**'

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Next", callback_data=f"next_{user_id}")]])
        try:
            msg = await event.reply_text(text, reply_markup=keyboard)
            await asyncio.sleep(300)  # 5 minutes = 300 seconds
            await event.delete()
            await msg.delete()
        except Exception as e:
            print(f"Error sending message: {e}")

    elif message.sticker:
        await event.reply_sticker(message.sticker.file_id)
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Next", callback_data=f"next_{user_id}")]])
        sticker_msg = await event.reply_sticker(sticker=message.sticker.file_id, reply_markup=keyboard)
        await asyncio.sleep(5)
        await sticker_msg.delete()

    else:
        await event.reply_text("Unsupported message type.")

@Bot.on_callback_query(filters.regex("^next_"))
async def next_message(bot, query: CallbackQuery):
    user_id = int(query.data.split("_")[1])
    current_index[user_id] += 1
    await query.message.delete()  # Delete the "Next" button message
    await display_message(query.message, user_id)  # Call display_message with the original message object

@Bot.on_callback_query()
async def button(bot, cmd: CallbackQuery):
    cb_data = cmd.data
    if "About_msg" in cb_data:
        await cmd.message.edit(
            text=Config.ABOUT_BOT_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Updates Channel", url="https://t.me/LazyDeveloper")
                    ],
                    [
                        InlineKeyboardButton("Connect Admin", url="https://t.me/LazyDeveloper"),
                        InlineKeyboardButton("ðŸ Home", callback_data="gohome")
                    ]
                ]
            ),
            parse_mode="html"
        )
    elif "Help_msg" in cb_data:
        await cmd.message.edit(
            text=Config.ABOUT_HELP_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [   InlineKeyboardButton("Help", callback_data="Help_msg"),
                        InlineKeyboardButton("Updates Channel", url="https://t.me/LazyDeveloper")
                    ],
                    [
                        InlineKeyboardButton("Connect Admin", url="https://t.me/LazyDeveloper"),
                        InlineKeyboardButton("ðŸ Home", callback_data="gohome")
                    ]
                ]
            ),
            parse_mode="html"
        )
    elif "gohome" in cb_data:
        await cmd.message.edit(
            text=Config.START_MSG.format(cmd.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Help", callback_data="Help_msg"),
                        InlineKeyboardButton("About", callback_data="About_msg")
                    ],
                    [
                        InlineKeyboardButton("Support Channel", url="https://t.me/LazyPrincessSupport"),
                    ]
                ]
            ),
            parse_mode="html"
        )

# Start Clients
Bot.start()
User.start()
# Loop Clients till Disconnects
idle()
# After Disconnects,
# Stop Clients
Bot.stop()
User.stop()
