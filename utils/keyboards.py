"""
Keyboard builders for the OCR Telegram Bot.
"""
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from consts import DEFAULT_INTERFACE_LANG
from localization import get_text, get_supported_languages


def get_user_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    """
    Get user's interface language from context.

    :param context: Context object containing user_data
    :return: Language code ('uk' or 'en')
    """
    return context.user_data.get('interface_lang', DEFAULT_INTERFACE_LANG)


def get_interface_language_keyboard() -> ReplyKeyboardMarkup:
    """
    Create keyboard for interface language selection.

    :return: ReplyKeyboardMarkup with language buttons
    """
    keyboard = [[
        KeyboardButton('Українська 🇺🇦'),
        KeyboardButton('English 🇬🇧')
    ]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_main_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    """
    Create main menu keyboard with language options.

    :param context: Context object for localization
    :return: ReplyKeyboardMarkup with main menu buttons
    """
    lang = get_user_lang(context)
    keyboard = [
        [
            KeyboardButton(get_text(lang, 'btn_ukrainian')),
            KeyboardButton(get_text(lang, 'btn_english')),
            KeyboardButton(get_text(lang, 'btn_other_language'))
        ],
        [KeyboardButton(get_text(lang, 'btn_multiple_languages'))],
        [
            KeyboardButton(get_text(lang, 'btn_info')),
            KeyboardButton(get_text(lang, 'btn_interface_language'))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_text_delivery_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    """
    Create keyboard for text delivery method selection.

    :param context: Context object for localization
    :return: ReplyKeyboardMarkup with delivery option buttons
    """
    lang = get_user_lang(context)
    keyboard = [[
        KeyboardButton(get_text(lang, 'btn_message')),
        KeyboardButton(get_text(lang, 'btn_text_file'))
    ]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_language_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    """
    Create keyboard with all supported OCR languages and navigation buttons.

    :param context: Context object for localization
    :return: ReplyKeyboardMarkup with language buttons
    """
    lang = get_user_lang(context)
    supported_langs = get_supported_languages(lang)

    keyboard = [[KeyboardButton(get_text(lang, 'btn_back_to_menu'))]]

    if context.user_data.get('lang_confirm_state'):
        keyboard.insert(0, [KeyboardButton(get_text(lang, 'btn_confirm'))])

    keyboard.extend([[KeyboardButton(lang_name)] for lang_name in supported_langs.keys()])

    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
