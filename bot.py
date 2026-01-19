"""
OCR Telegram Bot - Main Entry Point
====================================

This module is the main entry point for the OCR Telegram Bot.
It initializes logging, loads configuration, and starts the bot.

Bot Flow:
---------
1. /start → Interface language selection
2. OCR language selection
3. File upload
4. Delivery method choice (message or file)
5. OCR processing and result delivery

For handler implementations, see the handlers/ package.
For utility functions, see the utils/ package.
"""
import os
import sys

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError

from localization import TRANSLATIONS
from utils import setup_logger, create_translation_filter, create_multi_key_filter
from handlers import start, handle_info, handle_text_delivery_choice, handle_menu_navigation, handle_files


def main():
    """Initialize and run the bot."""
    # Setup logging
    logger = setup_logger()

    # Load environment variables
    load_dotenv()

    # Log startup info (translations already validated on import)
    logger.info('Application starting with %d supported interface languages', len(TRANSLATIONS))

    # Get bot token
    token = os.getenv('TOKEN')
    if not token:
        logger.critical("Environment variable TOKEN is not set or is empty. Check your .env file.")
        sys.exit(1)

    try:
        # Build application with concurrent updates for parallel processing
        app = ApplicationBuilder().token(token).concurrent_updates(True).build()

        # Register handlers
        app.add_handler(CommandHandler('start', start))
        app.add_handler(MessageHandler(
            filters.TEXT & create_translation_filter('btn_info'),
            handle_info
        ))
        app.add_handler(MessageHandler(
            filters.TEXT & create_multi_key_filter('btn_message', 'btn_text_file'),
            handle_text_delivery_choice
        ))
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_menu_navigation
        ))
        app.add_handler(MessageHandler(
            filters.Document.ALL,
            handle_files
        ))

        logger.info('Bot handlers registered successfully. Starting polling...')
        app.run_polling()

    except TelegramError as e:
        logger.critical('Telegram API error: %s', e, exc_info=True)
        sys.exit(1)
    except (OSError, RuntimeError) as e:
        logger.critical('Failed to start bot: %s', e, exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
