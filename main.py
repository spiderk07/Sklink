from configs import Config
from pyrogram import Client, filters, idle
from pyrogram.errors import QueryIdInvalid
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InlineQuery, InlineQueryResultArticle,InputTextMessageContent
from LazyDeveloper.forcesub import ForceSub
import asyncio
from spellchecker import SpellChecker  # Import the spellchecker library

# Bot Client for Inline Search
Bot = Client(
    Config.BOT_SESSION_NAME, # Use positional argument for session_name
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User Client for Searching in Channel.
User = Client(
    "user",  # Added a session name for the User client, use positional argument
    api_id=Config.API_ID,  # added api_id
    api_hash=Config.API_HASH,  # added api_hash
    session_string=Config.USER_SESSION_STRING # added session_string
)

# Initialize spell checker
spell = SpellChecker()

# Dictionary to store spellcheck suggestions for each user
suggestion_cache = {}

async def generate_spellcheck_suggestions(text):
    """Generates spellcheck suggestions for the given text."""
    words = text.split()
    misspelled = spell.unknown(words)
    suggestions = {}
    for word in misspelled:
        suggestions[word] = spell.candidates(word)
    return suggestions

async def create_spellcheck_keyboard(word, suggestions, index=0):
    """Creates an inline keyboard for spellcheck suggestions."""
    buttons = []
    if suggestions:
        suggestion_list = list(suggestions)
        if len(suggestion_list) > 1: #Only show next button if there are multiple suggestions
            buttons.append(InlineKeyboardButton(f"Next ({index + 1}/{len(suggestion_list)})", callback_data=f"next_suggestion:{word}:{index}"))
        
        #Add a button to accept the current suggestion
        buttons.append(InlineKeyboardButton(f"Accept", callback_data=f"accept_suggestion:{word}:{index}"))
    return InlineKeyboardMarkup([buttons])

@Bot.on_message(filters.private & filters.text & ~filters.command("start") & ~filters.command("help"))
async def spellcheck_handler(client, message):
    """Handles spell checking and suggestion display."""
    user_id = message.from_user.id
    text = message.text

    # Generate spellcheck suggestions
    suggestions = await generate_spellcheck_suggestions(text)

    if not suggestions:
        await message.reply_text("No spelling errors found.")
        return

    # Store suggestions in cache
    suggestion_cache[user_id] = suggestions
    
    for word, suggestion_set in suggestions.items():
        suggestion_list = list(suggestion_set)
        if suggestion_list:
            keyboard = await create_spellcheck_keyboard(word, suggestion_list)
            await message.reply_text(f"Did you mean '{suggestion_list[0]}' for '{word}'?", reply_markup=keyboard) #Show the first suggestion
        else:
            await message.reply_text(f"No suggestions found for '{word}'.")

@Bot.on_callback_query(filters.regex("^next_suggestion"))
async def next_suggestion_callback(client, callback_query):
    """Handles the 'Next' button callback."""
    user_id = callback_query.from_user.id
    _, word, index_str = callback_query.data.split(":")
    index = int(index_str)
    
    suggestions = suggestion_cache.get(user_id, {}).get(word)
    if not suggestions:
        await callback_query.answer("No more suggestions.")
        return

    suggestion_list = list(suggestions)
    next_index = (index + 1) % len(suggestion_list)  # Cycle through suggestions

    keyboard = await create_spellcheck_keyboard(word, suggestion_list, next_index)
    await callback_query.message.edit_text(f"Did you mean '{suggestion_list[next_index]}' for '{word}'?", reply_markup=keyboard) #Show the next suggestion
    await callback_query.answer()  # Acknowledge the callback

@Bot.on_callback_query(filters.regex("^accept_suggestion"))
async def accept_suggestion_callback(client, callback_query):
    """Handles accepting a suggestion."""
    user_id = callback_query.from_user.id
    _, word, index_str = callback_query.data.split(":")
    index = int(index_str)

    suggestions = suggestion_cache.get(user_id, {}).get(word)
    if not suggestions:
        await callback_query.answer("Suggestion not found.")
        return

    suggestion_list = list(suggestions)
    accepted_suggestion = suggestion_list[index]

    #Replace the word in the original message with the accepted suggestion
    original_text = callback_query.message.reply_to_message.text #Get original message
    new_text = original_text.replace(word, accepted_suggestion)

    await client.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.id,
        text=f"Original: {original_text}\nCorrected: {new_text}"
    )

    await callback_query.answer("Suggestion accepted!")

@Bot.on_message(filters.private & filters.command("start"))
async def start_handler(_, event: Message):
	await event.reply_photo("https://telegra.ph/file/2b160d9765fe080c704d2.png",
                                caption=Config.START_MSG.format(event.from_user.mention),
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("🔺 Donate us 🔺", url="https://p.paytm.me/xCTH/vo37hii9")],
                                    [InlineKeyboardButton("⚡️ LazyDeveloper ⚡️", url="https://t.me/LazyDeveloper")],
                                    [InlineKeyboardButton("🤒Help", callback_data="Help_msg"),
                                    InlineKeyboardButton("🦋About", callback_data="About_msg")]]))

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
    answers = f'**📂 Hunts For ➠ {event.text} \n⟥⟥⟥⟥⟥⟥⟥⟥⟥⟥⟥⟥⟥⟤\n🔊\n➠ Type Only Movie Name With Correct Spelling. Dont type Bhejo, Bhej Do, send me etc...✍️\n➠ Add Year For Better Result.🗓️\n⟥⟥⟥⟥⟥⟥⟥⟥⟥⟥⟥⟥⟥⟤\n\n**'
    async for message in User.search_messages(chat_id=Config.CHANNEL_ID, limit=50, query=event.text):
        if message.text:
            thumb = None
            f_text = message.text
            msg_text = message.text.html
            if "|||" in message.text:
                f_text = message.text.split("|||", 1)[0]
                msg_text = message.text.html.split("|||", 1)[0]
            answers += f'**🎞 Movie Title ➠ ' + '' + f_text.split("\n", 1)[0] + '' + '\n\n📜 Download URLs ➠ ' + '' + f_text.split("\n", 2)[-1] + ' \n\n▰▱▰▱▰▱▰▱▰▱▰▱▰▱\nLink Will Auto Delete In 35Sec...⏰\n▰▱▰▱▰▱▰▱▰▱▰▱▰▱\n\n**'
    try:
        msg = await event.reply_text(answers)
        await asyncio.sleep(35)
        await event.delete()
        await msg.delete()
    except:
        print(f"[{Config.BOT_SESSION_NAME}] - Failed to Answer - {event.from_user.first_name}")


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
						InlineKeyboardButton("🏠Home", callback_data="gohome")
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
						InlineKeyboardButton("🏠Home", callback_data="gohome")
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
