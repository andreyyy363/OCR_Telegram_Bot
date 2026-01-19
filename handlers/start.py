"""
Start command and interface language handlers.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from localization import get_text
from utils.keyboards import (
    get_user_lang,
    get_interface_language_keyboard,
    get_main_keyboard,
)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command - shows interface language selection first.

    :param update: Update object
    :param context: Context object
    """
    user_id = update.effective_user.id
    logger.info('User %s started the bot', user_id)
    context.user_data['awaiting_interface_lang'] = True
    await update.message.reply_text(
        get_text('uk', 'choose_interface_language'),
        reply_markup=get_interface_language_keyboard()
    )


async def handle_interface_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle interface language selection.

    :param update: Update object
    :param context: Context object
    :return: True if handled, False otherwise
    """
    user_id = update.effective_user.id
    choice = update.message.text

    if not context.user_data.get('awaiting_interface_lang'):
        return False

    if choice == 'Українська 🇺🇦':
        context.user_data['interface_lang'] = 'uk'
    elif choice == 'English 🇬🇧':
        context.user_data['interface_lang'] = 'en'
    else:
        return False

    context.user_data['awaiting_interface_lang'] = False
    lang = get_user_lang(context)
    logger.info('User %s set interface language to %s', user_id, lang)
    await update.message.reply_text(
        get_text(lang, 'interface_language_set'),
        reply_markup=get_main_keyboard(context)
    )
    await update.message.reply_text(
        get_text(lang, 'start_message'),
        reply_markup=get_main_keyboard(context)
    )
    return True
