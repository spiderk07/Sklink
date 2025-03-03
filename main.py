from configs import Config
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from imdb import IMDb  # IMDb API for movie search
import asyncio

# Initialize IMDb API
ia = IMDb()

# Bot Client for Inline Search
Bot = Client(
    Config.BOT_SESSION_NAME,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User Client for Searching in Channel.
User = Client(
    "user",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.USER_SESSION_STRING
)

# Dictionary to store search results for pagination
user_search_results = {}

@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, event: Message):
    await event.reply_photo(
        "https://telegra.ph/file/2b160d9765fe080c704d2.png",
        caption=Config.START_MSG.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔷 Donate", url="https://p.paytm.me/xCTH/vo37hii9")],
            [InlineKeyboardButton("⚡ LazyDeveloper", url="https://t.me/LazyDeveloper")],
            [InlineKeyboardButton("💡 Help", callback_data="Help_msg"),
             InlineKeyboardButton("📜 About", callback_data="About_msg")]
        ])
    )

@Bot.on_message(filters.private & filters.command("help"))
async def help_handler(_, event: Message):
    await event.reply_text(
        Config.ABOUT_HELP_TEXT.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Updates", url="https://t.me/LazyDeveloper"),
             InlineKeyboardButton("💬 Support Group", url="https://t.me/LazyPrincessSupport"),
             InlineKeyboardButton("ℹ About", callback_data="About_msg")]
        ])
    )

@Bot.on_message(filters.incoming)
async def search_movie(_, event: Message):
    if not event or not event.text:
        return
    
    query = event.text.strip()
    if query.startswith("/"):
        return

    user_id = event.from_user.id
    user_name = event.from_user.first_name or "User"
    
    try:
        search_results = ia.search_movie(query)
        if not search_results:
            await event.reply_text(f"❌ No results found for '{query}'")
            return
        
        user_search_results[user_id] = search_results  # Store results for pagination
        total_results = len(search_results)
        first_result = search_results[0]
        movie_title = first_result["title"]

        # Inline button to search in the channel
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔍 Search '{movie_title}'", callback_data=f"search_{user_id}_0")],
            [InlineKeyboardButton("➡ Next", callback_data=f"next_{user_id}_1") if total_results > 1 else None]
        ].filter(None))

        await event.reply_text(
            f"🎬 **{movie_title}**\n\nTotal Results: **{total_results}**\nClick below to search in the channel:",
            reply_markup=reply_markup
        )

    except Exception as e:
        await event.reply_text(f"⚠️ Error: {str(e)}")

@Bot.on_callback_query()
async def handle_callback(bot, cmd: CallbackQuery):
    cb_data = cmd.data
    user_id = cmd.from_user.id

    if cb_data.startswith("search_"):
        _, user_id, index = cb_data.split("_")
        index = int(index)

        if user_id in user_search_results:
            search_results = user_search_results[user_id]
            if index < len(search_results):
                movie_title = search_results[index]["title"]
                await cmd.message.edit_text(
                    f"🔍 Searching for **{movie_title}**...",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Search Again", callback_data=f"search_{user_id}_{index}")],
                        [InlineKeyboardButton("➡ Next", callback_data=f"next_{user_id}_{index + 1}") if index + 1 < len(search_results) else None]
                    ].filter(None))
                )
                await search_in_channel(cmd.message, movie_title)
        else:
            await cmd.answer("❌ No results stored. Please search again.")

    elif cb_data.startswith("next_"):
        _, user_id, index = cb_data.split("_")
        index = int(index)

        if user_id in user_search_results:
            search_results = user_search_results[user_id]
            if index < len(search_results):
                movie_title = search_results[index]["title"]

                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🔍 Search '{movie_title}'", callback_data=f"search_{user_id}_{index}")],
                    [InlineKeyboardButton("➡ Next", callback_data=f"next_{user_id}_{index + 1}") if index + 1 < len(search_results) else None]
                ].filter(None))

                await cmd.message.edit_text(
                    f"🎬 **{movie_title}**\n\nClick below to search in the channel:",
                    reply_markup=reply_markup
                )
        else:
            await cmd.answer("❌ No results stored. Please search again.")

async def search_in_channel(event, query):
    answers = f'**Powered By @Skfilmbox**\n\n'
    async for message in User.search_messages(chat_id=Config.CHANNEL_ID, limit=10, query=query):
        if message.text:
            title = message.text.split("\n", 1)[0]
            description = message.text.split("\n", 2)[-1]
            answers += f'🎬 **{title}**\n\n{description}\n\n'

    if answers.strip() == '**Powered By @Skfilmbox**\n\n':
        answers += "❌ No results found in the channel."

    try:
        msg = await event.reply_text(answers)
        await asyncio.sleep(35)
        await event.delete()
        await msg.delete()
    except:
        print(f"[{Config.BOT_SESSION_NAME}] - Failed to send response")

# Start Clients
Bot.start()
User.start()
idle()
Bot.stop()
User.stop()
