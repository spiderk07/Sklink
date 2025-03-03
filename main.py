from configs import Config
from pyrogram import Client, filters, idle
from pyrogram.errors import QueryIdInvalid
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
from imdb import IMDb  # Import IMDbPY package

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

# Initialize IMDbPY
ia = IMDb()

# Store search results and current index for each user
user_search_results = {}

@Bot.on_message(filters.private)
async def search_handler(_, event: Message):
    # Don't process messages that start with '/'
    if event.text.startswith("/"):
        return

    query = event.text
    results = []

    if query.lower().startswith("imdb "):  # If the user sends a query starting with "imdb "
        # Remove the "imdb " prefix
        movie_name = query[5:]
        
        try:
            # Search for movies in IMDb
            search_results = ia.search_movie(movie_name)

            if search_results:
                # Get the first result
                movie = search_results[0]
                title = movie['title']
                year = movie['year']

                # Create an inline button for the movie title
                button = InlineKeyboardButton(f"{title} ({year})", callback_data=f"imdb_search_{movie['movieID']}")

                reply_markup = InlineKeyboardMarkup([[button]])

                # Send the result (movie name and year) to the user
                await event.reply_text(f"Found movie: **{title} ({year})**", reply_markup=reply_markup)
            else:
                await event.reply_text("No movie found with that name.")
        except Exception as e:
            await event.reply_text(f"Error occurred while fetching data from IMDb: {str(e)}")
    
    else:
        # Default search in the channel when the user sends a normal query
        async for message in User.search_messages(chat_id=Config.CHANNEL_ID, limit=50, query=query):
            if message.text:
                results.append({
                    'text': message.text,
                    'user': message.from_user.first_name,
                    'date': message.date,
                    'message_id': message.message_id
                })

        if results:
            # Save the search results and set the current index to 0
            user_search_results[event.from_user.id] = {
                'results': results,
                'current_index': 0  # Starting at the first result
            }
            await send_search_result(event, results[0], 0)
        else:
            await event.reply_text("No results found for your query.")

async def send_search_result(event: Message, result, index: int):
    """
    Send the result at the current index, with 'Next' and 'Previous' buttons.
    """
    next_index = index + 1
    prev_index = index - 1

    buttons = []
    
    if prev_index >= 0:
        buttons.append(InlineKeyboardButton("Previous", callback_data=f"prev_{index}"))
    if next_index < len(user_search_results[event.from_user.id]['results']):
        buttons.append(InlineKeyboardButton("Next", callback_data=f"next_{index}"))

    reply_markup = InlineKeyboardMarkup([buttons])

    result_text = f"**{result['text'].splitlines()[0]}**\nBy {result['user']} on {result['date']}\n\n*{result['text']}*"
    
    # Reply with the result and buttons for navigation
    await event.reply_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode="markdown"
    )

@Bot.on_callback_query()
async def callback_query_handler(_, cmd: CallbackQuery):
    user_id = cmd.from_user.id
    data = cmd.data

    if user_id not in user_search_results:
        return

    search_data = user_search_results[user_id]
    results = search_data['results']
    current_index = search_data['current_index']

    # If 'Next' button was clicked
    if data.startswith("next_"):
        new_index = current_index + 1
        if new_index < len(results):
            search_data['current_index'] = new_index
            await send_search_result(cmd.message, results[new_index], new_index)

    # If 'Previous' button was clicked
    elif data.startswith("prev_"):
        new_index = current_index - 1
        if new_index >= 0:
            search_data['current_index'] = new_index
            await send_search_result(cmd.message, results[new_index], new_index)

    # If IMDb search button was clicked
    elif data.startswith("imdb_search_"):
        movie_id = data.split("_")[-1]

        try:
            # Get the movie details using the IMDb ID
            movie = ia.get_movie(movie_id)
            title = movie['title']
            year = movie['year']
            plot = movie.get('plot', ['No plot available'])[0]

            # Send the detailed information of the movie
            await cmd.message.edit(
                text=f"**{title} ({year})**\n\n{plot}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Search in Channel", callback_data=f"search_in_channel_{title}")],
                    [InlineKeyboardButton("Back", callback_data="gohome")]
                ])
            )
        except Exception as e:
            await cmd.answer("Error occurred while fetching movie details.")
            print(f"Error fetching IMDb details: {e}")
    
    # Acknowledge the callback
    await cmd.answer()

@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, event: Message):
    await event.reply_photo("https://telegra.ph/file/2b160d9765fe080c704d2.png",
                            caption=Config.START_MSG.format(event.from_user.mention),
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("💰 Donate us 💰", url="https://p.paytm.me/xCTH/vo37hii9")],
                                [InlineKeyboardButton("💻 LazyDeveloper 💻", url="https://t.me/LazyDeveloper")],
                                [InlineKeyboardButton("😕Help", callback_data="Help_msg"),
                                 InlineKeyboardButton("📝About", callback_data="About_msg")]]))

@Bot.on_message(filters.private & filters.command("help"))
async def help_handler(_, event: Message):
    await event.reply_text(Config.ABOUT_HELP_TEXT.format(event.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Updates", url="https://t.me/LazyDeveloper"),
             InlineKeyboardButton("Support Group", url="https://t.me/LazyPrincessSupport"),
             InlineKeyboardButton("About", callback_data="About_msg")]
        ])
    )

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
                        InlineKeyboardButton("🏠 Home", callback_data="gohome")
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
                    [InlineKeyboardButton("Help", callback_data="Help_msg"),
                     InlineKeyboardButton("Updates Channel", url="https://t.me/LazyDeveloper")
                    ],
                    [
                        InlineKeyboardButton("Connect Admin", url="https://t.me/LazyDeveloper"),
                        InlineKeyboardButton("🏠 Home", callback_data="gohome")
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
