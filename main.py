from configs import Config
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
from imdb import IMDb  

# Bot Client
Bot = Client(
    Config.BOT_SESSION_NAME,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User Client for Channel Search
User = Client(
    "user",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.USER_SESSION_STRING
)

# IMDb Instance
ia = IMDb()

# Dictionary to store search results for pagination
search_results_cache = {}

@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, event: Message):
    await event.reply_photo(
        "https://telegra.ph/file/2b160d9765fe080c704d2.png",
        caption=Config.START_MSG.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Donate", url="https://p.paytm.me/xCTH/vo37hii9")],
            [InlineKeyboardButton("⚡ LazyDeveloper", url="https://t.me/LazyDeveloper")],
            [InlineKeyboardButton("💡 Help", callback_data="Help_msg"),
             InlineKeyboardButton("📖 About", callback_data="About_msg")]
        ])
    )

@Bot.on_message(filters.private)
async def movie_search(_, event: Message):
    query = event.text.strip()
    if not query:
        return

    # Search IMDb
    try:
        search_results = ia.search_movie(query)

        if search_results:
            movie = search_results[0]  # Get first result
            title = movie['title']

            # Inline button to search in the channel
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🔍 Search '{title}'", callback_data=f"search_{title}_0")]
            ])

            await event.reply_text(f"Found movie: **{title}**\nClick below to search in the channel:", reply_markup=reply_markup)

        else:
            await event.reply_text("❌ No movie found. Try again.")

    except Exception as e:
        await event.reply_text(f"⚠️ Error fetching IMDb data: {str(e)}")

@Bot.on_callback_query()
async def callback_query_handler(_, cmd: CallbackQuery):
    data = cmd.data

    if data.startswith("search_"):
        parts = data.split("_", 2)
        movie_name = parts[1]
        index = int(parts[2])

        # If not cached, fetch results
        if movie_name not in search_results_cache:
            results = []
            async for message in User.search_messages(chat_id=Config.CHANNEL_ID, limit=50, query=movie_name):
                if message.text:
                    results.append(message.text)
            search_results_cache[movie_name] = results

        results = search_results_cache.get(movie_name, [])
        total_results = len(results)

        if results and index < total_results:
            # Show current result with heading
            result_text = f"**Result {index+1} of {total_results}**\n\n{results[index]}"

            # Buttons for navigation
            buttons = []
            if index > 0:
                buttons.append(InlineKeyboardButton("⬅ Previous", callback_data=f"search_{movie_name}_{index-1}"))
            if index + 1 < total_results:
                buttons.append(InlineKeyboardButton("➡ Next", callback_data=f"search_{movie_name}_{index+1}"))

            await cmd.message.edit(result_text, reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None)

        else:
            await cmd.message.edit(f"❌ No more results for '{movie_name}'.")

# Start Clients
Bot.start()
User.start()
idle()
Bot.stop()
User.stop()
