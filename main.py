from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio

# Bot Client
Bot = Client(
    "bot_session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User Client for Searching in Channel
User = Client(
    "user_session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    session_string=Config.USER_SESSION_STRING
)

# Store search results and current index for each user
user_search_results = {}

@Bot.on_message(filters.private)
async def search_handler(_, event: Message):
    # Only search if the message is not a command
    if event.text.startswith("/"):
        return

    query = event.text
    results = []

    # Search for messages in the channel matching the query
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

    # Acknowledge the callback
    await cmd.answer()

# Start Clients
Bot.start()
User.start()
Bot.idle()

# Stop Clients after disconnection
Bot.stop()
User.stop()
