import os

class Config:
    # Telegram API credentials
    API_ID = int(os.environ.get("API_ID", "27967371"))
    API_HASH = os.environ.get("API_HASH", "c8c22d9e427b8589236a6cd94a82a244")

    # Bot token
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "6922466504:AAGKesha1FoDfa52BX32gYqE9V-TLKdpA_Y")
    BOT_SESSION_NAME = os.environ.get("BOT_SESSION_NAME", "SkFilmBot")

    # User session string (for searching in channel)
    USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", "BQGqv4sAxvmjqnc2CY4QqnaNZOt-T3F4DYrM0tyX5LnRaPFy64pJaqLekgLtf8bIglqnorz-fRxxMimtM6oZMuekL6fs_4yOhOyTos22QVlRdcGG-qeGbK0mR7YwuWl8EmOj-OBAiqjGv1eYiMpcIhu1vrTCJGb2b2JzYv7CSd43_jC2tTSPne3Qbo_HSSuShWIa287ckUFbtZi10jPmM2KR3YjIzhCWEs5LtSB8gYM_BBpDxaVIzirS4pbOvI0b1rk2H0tiCfI72g0VqM6xmTv3B8PUc_GeZU2zXXl-nT9LjTYlTeFKa_rozq_WoMB-QcmpXg1JUe016Lj8FwBKXZqxOG9LrwAAAAGp21jFAA")

    # Channel ID where the bot searches for content
    CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1001234567890"))

    # Start message
    START_MSG = os.environ.get("START_MSG", "Hello {}, I'm a bot!")

    # About help text
    ABOUT_HELP_TEXT = os.environ.get("ABOUT_HELP_TEXT", "Help text here")

    # About bot text
    ABOUT_BOT_TEXT = os.environ.get("ABOUT_BOT_TEXT", "About bot text here")
