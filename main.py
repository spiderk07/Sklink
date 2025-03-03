import os
from pyrogram import Client, filters
from pyrogram.errors import QueryIdInvalid
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from LazyDeveloper.forcesub import ForceSub
import asyncio

# Bot Client for Inline Search
Bot = Client(
    session_name="bot_session",  # Shorter session name for the bot
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User Client for Searching in Channel
User = Client(
    session_name="user_session",  # Shorter session name for the user
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.USER_SESSION_STRING
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
        disable_web_page_preview=True,
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
    async for message in User.search_messages(chat_id=Config.CHANNEL_ID, limit=50, query=event.text):
        if message.text:
            f_text = message.text
            msg_text = message.text.html
            if "|||" in message.text:
                f_text = message.text.split("|||", 1)[0]
                msg_text = message.text.html.split("|||", 1)[0]
            answers = f'**🎞 Movie Title ➠ {f_text}'
            try:
                thumb = None
                thumb = message.photo.file_id
            except:
                pass
            msg = await event.reply_text(answers)
            await asyncio.sleep(35)
            await msg.delete()

@Bot.on_callback_query()
async def button(bot, cmd: CallbackQuery):
    cb_data = cmd.data
    if "Help_msg" in cb_data:
        await cmd.message.edit(
            text=Config.ABOUT_HELP_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Updates", url="https://t.me/LazyDeveloper"),
                 InlineKeyboardButton("Support Group", url="https://t.me/LazyPrincessSupport"),
                 InlineKeyboardButton("About", callback_data="About_msg")]
            ])
        )
    elif "About_msg" in cb_data:
        await cmd.message.edit(
            text=Config.ABOUT_BOT_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Updates", url="https://t.me/LazyDeveloper"),
                 InlineKeyboardButton("Support Group", url="https://t.me/LazyPrincessSupport"),
                 InlineKeyboardButton("Help", callback_data="Help_msg")]
            ])
        )

if __name__ == "__main__":
    Bot.run()
    User.run()
