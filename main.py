import asyncio
import re
from pyrogram import Client, filters
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import QueryIdInvalid
from LazyDeveloper.forcesub import ForceSub
from configs import Config

RESULTS_PER_PAGE = 1  # Show one result per page

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

# Function to replace Telegram links with your specific username
def replace_telegram_links(text):
    # Regular expression to match any Telegram link and replace it with your username link
    return re.sub(r'https?://t\.me/[^\s]+', 'https://t.me/skfilmbox', text)

@Client.on_inline_query()
async def inline_query_handler(bot, query):
    # Check if the user is subscribed
    f_sub = await ForceSub(bot, query.from_user)
    if not f_sub:
        return

    # Query string sent by the user
    user_query = query.query.strip()
    if not user_query:
        return  # No query, nothing to process

    channels = (await get_group(query.from_user.id))["channels"]
    if not channels:
        return  # No channels to search in

    header = "<b><i>★ Powered by:@Skcreator70</i></b>\n\n"
    footer = (
        "<a href='https://whatsapp.com/channel/0029Va69Ts2C6ZvmEWsHNo3c'>☛ 𝙅𝙤𝙞𝙣 𝙒𝙝𝙖𝙩𝙨𝘼𝙥𝙥 𝘾𝙝𝙖𝙣𝙣𝙚𝙡</a>\n"
        "<i>Cʟɪᴄᴋ ᴏɴ Nᴇxᴛ Bᴜᴛᴛᴏɴ Tᴏ Gᴏ Tᴏ Nᴇxᴛ Pᴀɢᴇ ☟</i>"
    )

    try:
        found_results = []
        for channel in channels:
            async for msg in bot.search_messages(chat_id=channel, query=user_query):
                name = msg.text or msg.caption
                if name and name not in found_results:
                    # Replace Telegram links in the result
                    found_results.append(replace_telegram_links(name))

        if found_results:
            total_results = len(found_results)
            head = f"{header}🔍 <b>Total Results Found: {total_results}</b>\n\n"
        else:
            # Fallback if no results found
            movies = await search_imdb(user_query)
            buttons = [
                [InlineKeyboardButton(movie['title'], callback_data=f"recheck_{movie['id']}")] for movie in movies
            ]
            
            results = "<b><i>Sorry, no results found for your query 😕.\nDid you mean any of these?</i></b>"
            results_markup = InlineKeyboardMarkup(buttons)

            # Sending an inline query response
            await bot.answer_inline_query(
                query.id,
                results=[
                    InlineQueryResultArticle(
                        title="No Results",
                        input_message_content=InputTextMessageContent(results),
                        reply_markup=results_markup
                    )
                ]
            )
            return

        # Show the first result in the inline query response
        page_result = found_results[0]  # Since we're showing one result per page
        result_message = f"<b><i>🎬 {page_result}</i></b>\n\n{footer}"

        buttons = [
            InlineKeyboardButton("⏪ Previous", callback_data=f"page_1_{user_query}"),
            InlineKeyboardButton("Next ⏭", callback_data=f"page_2_{user_query}")
        ]
        reply_markup = InlineKeyboardMarkup([buttons])

        # Sending the inline query result
        await bot.answer_inline_query(
            query.id,
            results=[
                InlineQueryResultArticle(
                    title="Search Result",
                    input_message_content=InputTextMessageContent(result_message, disable_web_page_preview=True),
                    reply_markup=reply_markup
                )
            ]
        )

    except Exception as e:
        print(f"Error occurred in inline query handler: {e}")
        await bot.answer_inline_query(query.id, results=[], switch_pm_text="An error occurred. Please try again later.", switch_pm_parameter="error")


@Client.on_callback_query(filters.regex(r"^page"))
async def page_navigation(bot, update):
    try:
        data = update.data.split("_")
        page_number = int(data[1])
        query = data[2]

        channels = (await get_group(update.message.chat.id))["channels"]
        found_results = []

        for channel in channels:
            async for msg in bot.search_messages(chat_id=channel, query=query):
                name = msg.text or msg.caption
                if name and name not in found_results:
                    # Replace Telegram links in the result
                    found_results.append(replace_telegram_links(name))

        start_idx = (page_number - 1) * RESULTS_PER_PAGE
        if start_idx >= len(found_results):
            await update.answer("No more results available.", show_alert=True)
            return

        # Delete the current message (first page or previous page)
        await update.message.delete()

        # Show temporary sticker
        sticker_id = "CAACAgIAAxkBAAIrCGUwjom4s9P26nsiP-QAAUV-qDDOhQACcQgAAoSUQUlvaAkaprvOczAE"
        sticker_msg = await bot.send_sticker(chat_id=update.message.chat.id, sticker=sticker_id)
        await asyncio.sleep(2)  # Display sticker for 2 seconds
        await sticker_msg.delete()  # Remove sticker after 2 seconds

        # Prepare and show the next page
        page_result = found_results[start_idx]
        results = f"<b><i>🎬 {page_result}</i></b>\n\n<a href='https://whatsapp.com/channel/0029Va69Ts2C6ZvmEWsHNo3c'>☛ 𝙅𝙤𝙞𝙣 𝙒𝙝𝙖𝙩𝙨𝘼𝙥𝙥 𝘾𝙝𝙖𝙣𝙣𝙚𝙡</a>\n<i>Cʟɪᴄᴋ ᴏɴ Nᴇxᴛ Bᴜᴛᴛᴏɴ Tᴏ Gᴏ Tᴏ Nᴇxᴛ Pᴀɢᴇ ☟</i>"

        buttons = []
        if page_number > 1:
            buttons.append(InlineKeyboardButton("⏪ Previous", callback_data=f"page_{page_number - 1}_{query}"))
        if start_idx + RESULTS_PER_PAGE < len(found_results):
            buttons.append(InlineKeyboardButton("Next ⏭", callback_data=f"page_{page_number + 1}_{query}"))

        new_msg = await bot.send_message(
            chat_id=update.message.chat.id,
            text=results,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None
        )

        # Schedule the next page message for auto-deletion
        await save_dlt_message(bot, new_msg, 300)

    except Exception as e:
        print(f"Error occurred in pagination: {e}")
        await update.answer("An error occurred while fetching the page. Please try again later.", show_alert=True)
