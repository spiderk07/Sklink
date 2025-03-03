import os

class Config:
    # Telegram API credentials
    API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
    API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")

    # Bot token
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
    BOT_SESSION_NAME = os.environ.get("BOT_SESSION_NAME", "SkFilmBot")

    # User session string (for searching in channel)
    USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", "YOUR_USER_SESSION_STRING")

    # Channel ID where the bot searches for content
    CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1001234567890"))

    # Start message
    START_MSG = os.environ.get("START_MSG", "Hello {}, I'm a bot!")

    # About help text
    ABOUT_HELP_TEXT = os.environ.get("ABOUT_HELP_TEXT", "Help text here")

    # About bot text
    ABOUT_BOT_TEXT = os.environ.get("ABOUT_BOT_TEXT", "About bot text here")
