# in & as LazyDeveloper
# Please Don't Remove Credit

from configs import Config
from pyrogram import Client, filters, idle
from pyrogram.errors import QueryIdInvalid
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
import time

# Ensure system time is correct
async def sync_time():
    await asyncio.sleep(5)  # Small delay to sync time
    time.time()  # Get system time to fix "msg_id too low" error

asyncio.run(sync_time())

# Bot Client for Inline Search
Bot = Client(
    session_name=Config.BOT_SESSION_NAME,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    auto_sleep=True  # Fixes time desync issues
)

# User Client for Searching in Channel
User = Client(
    session_name=Config.USER_SESSION_STRING,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    auto_sleep=True  # Prevents disconnection
)

@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, event: Message):
    await event.reply_photo(
        "https://telegra.ph/file/2b160d9765fe080c704d2.png",
        caption=Config.START_MSG.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔺 Donate us 🔺", url="https://p.paytm.me/xCTH/vo37hii9")],
            [InlineKeyboardButton("⚡️ LazyDeveloper ⚡️", url="https://t.me/LazyDeveloper")],
            [InlineKeyboardButton("🤒Help", callback_data="Help_msg"),
             InlineKeyboardButton("🦋About", callback_data="About_msg")]
        ])
    )

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

@Bot.on_message(filters.text & filters.private)
async def inline_handlers(_, event: Message):
    query = event.text.strip()
    if query == '/start':
        return
    
    answers = f'**📂 Searching for ➠ {query}**\n\n'
    
    async for message in User.search_messages(chat_id=Config.CHANNEL_ID, limit=50, query=query):
        if message.text:
            f_text = message.text.split("|||", 1)[0] if "|||" in message.text else message.text
            answers += f'🎞 **Movie Title:** {f_text.splitlines()[0]}\n'
            answers += f'📜 **Download URLs:** {f_text.splitlines()[-1]}\n'
            answers += '⏰ **Links auto-delete in 35s**\n\n'
    
    try:
        msg = await event.reply_text(answers)
        await asyncio.sleep(35)
        await msg.delete()
        await event.delete()
    except:
        print(f"[{Config.BOT_SESSION_NAME}] - Failed to Answer - {event.from_user.first_name}")

@Bot.on_callback_query()
async def button(bot, cmd: CallbackQuery):
    cb_data = cmd.data
    if "About_msg" in cb_data:
        await cmd.message.edit(
            text=Config.ABOUT_BOT_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Updates Channel", url="https://t.me/LazyDeveloper")],
                [InlineKeyboardButton("Connect Admin", url="https://t.me/LazyDeveloper"),
                 InlineKeyboardButton("🏠Home", callback_data="gohome")]
            ]),
            parse_mode="html"
        )
    elif "Help_msg" in cb_data:
        await cmd.message.edit(
            text=Config.ABOUT_HELP_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Help", callback_data="Help_msg"),
                 InlineKeyboardButton("Updates Channel", url="https://t.me/LazyDeveloper")],
                [InlineKeyboardButton("Connect Admin", url="https://t.me/LazyDeveloper"),
                 InlineKeyboardButton("🏠Home", callback_data="gohome")]
            ]),
            parse_mode="html"
        )
    elif "gohome" in cb_data:
        await cmd.message.edit(
            text=Config.START_MSG.format(cmd.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Help", callback_data="Help_msg"),
                 InlineKeyboardButton("About", callback_data="About_msg")],
                [InlineKeyboardButton("Support Channel", url="https://t.me/LazyPrincessSupport")]
            ]),
            parse_mode="html"
        )

# Start Clients
Bot.start()
User.start()
idle()  # Keep bot running
Bot.stop()
User.stop()
