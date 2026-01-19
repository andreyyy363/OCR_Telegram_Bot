"""
Menu navigation and language selection handlers.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from localization import get_text, get_supported_languages
from utils.keyboards import (get_user_lang, get_main_keyboard, get_language_keyboard, get_text_delivery_keyboard,
                             get_interface_language_keyboard)
from .start import handle_interface_language_choice

logger = logging.getLogger(__name__)


async def _handle_confirm_choice(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lang: str,
        supported_langs: dict
) -> bool:
    """
    Handle confirm button in multi-language selection mode.

    :param update: Update object
    :param context: Context object
    :param lang: User's interface language
    :param supported_langs: Dictionary of supported languages
    :return: True if handled, False otherwise
    """
    user_id = update.effective_user.id
    context.user_data['lang_confirm_state'] = False
    lang_selection = context.user_data.get('lang_selection', [])

    if lang_selection:
        final_lang_string = '+'.join(lang_selection)
        context.user_data['ocr_lang_choice'] = final_lang_string
        lang_names = [k for k, v in supported_langs.items() if v in lang_selection]
        logger.info('User %s selected multiple OCR languages: %s', user_id, final_lang_string)
        await update.message.reply_text(
            get_text(lang, 'selected_languages', langs=str(lang_names))
        )
    else:
        logger.warning('User %s confirmed without selecting any language', user_id)
        await update.message.reply_text(get_text(lang, 'no_language_selected'))

    return True


async def _handle_multi_lang_selection(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lang: str,
        choice: str,
        supported_langs: dict
) -> bool:
    """
    Handle language selection in multi-language mode.

    :param update: Update object
    :param context: Context object
    :param lang: User's interface language
    :param choice: User's choice
    :param supported_langs: Dictionary of supported languages
    :return: True if handled, False otherwise
    """
    choice_lower = choice.lower()
    if choice_lower in supported_langs:
        ocr_code = supported_langs[choice_lower]
        lang_selection = context.user_data.get('lang_selection', [])

        if ocr_code not in lang_selection:
            lang_selection.append(ocr_code)
            context.user_data['lang_selection'] = lang_selection

        await update.message.reply_text(
            get_text(lang, 'language_added', lang=choice),
            reply_markup=get_language_keyboard(context)
        )
        return True

    return False


async def _handle_single_lang_choice(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lang: str,
        choice: str,
        supported_langs: dict
) -> bool:
    """
    Handle single language selection.

    :param update: Update object
    :param context: Context object
    :param lang: User's interface language
    :param choice: User's choice
    :param supported_langs: Dictionary of supported languages
    :return: True if handled, False otherwise
    """
    user_id = update.effective_user.id
    choice_lower = choice.lower()
    lang_map = {
        get_text(lang, 'btn_ukrainian'): 'ukr',
        get_text(lang, 'btn_english'): 'eng',
    }

    if choice in lang_map:
        context.user_data['ocr_lang_choice'] = lang_map[choice]
        logger.info('User %s selected OCR language: %s', user_id, lang_map[choice])
        await update.message.reply_text(get_text(lang, 'language_selected', lang=choice))
        return True

    if choice_lower in supported_langs:
        context.user_data['ocr_lang_choice'] = supported_langs[choice_lower]
        logger.info('User %s selected OCR language: %s', user_id, supported_langs[choice_lower])
        await update.message.reply_text(get_text(lang, 'language_selected', lang=choice))
        return True

    return False


async def _handle_menu_buttons(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        lang: str,
        choice: str
) -> bool:
    """
    Handle menu navigation buttons.

    :param update: Update object
    :param context: Context object
    :param lang: User's interface language
    :param choice: User's choice
    :return: True if handled, False otherwise
    """
    if choice == get_text(lang, 'btn_other_language'):
        await update.message.reply_text(
            get_text(lang, 'choose_language'),
            reply_markup=get_language_keyboard(context)
        )
        return True

    if choice == get_text(lang, 'btn_multiple_languages'):
        context.user_data['lang_confirm_state'] = True
        context.user_data['lang_selection'] = []
        await update.message.reply_text(
            get_text(lang, 'choose_multiple_languages'),
            reply_markup=get_language_keyboard(context)
        )
        return True

    if choice == get_text(lang, 'btn_back_to_menu'):
        context.user_data['lang_confirm_state'] = False
        await update.message.reply_text(
            get_text(lang, 'choose_alphabet'),
            reply_markup=get_main_keyboard(context)
        )
        return True

    return False


async def _show_fallback_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """
    Show appropriate keyboard when no handler matched the input.

    Determines the correct keyboard based on current user state.

    :param update: Update object
    :param context: Context object
    :param lang: User's interface language
    """
    if context.user_data.get('awaiting_delivery_choice'):
        await update.message.reply_text(
            get_text(lang, 'please_choose_delivery'),
            reply_markup=get_text_delivery_keyboard(context)
        )
    elif context.user_data.get('lang_confirm_state'):
        await update.message.reply_text(
            get_text(lang, 'please_choose_language'),
            reply_markup=get_language_keyboard(context)
        )
    else:
        await update.message.reply_text(
            get_text(lang, 'please_choose_alphabet'),
            reply_markup=get_main_keyboard(context)
        )


async def handle_menu_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle menu navigation and language selection.

    Routes user input to appropriate handlers based on current state.
    Uses early returns to reduce complexity.

    :param update: Update object
    :param context: Context object
    """
    choice = update.message.text
    lang = get_user_lang(context)
    supported_langs = get_supported_languages(lang)

    # Priority 1: Interface language selection in progress
    if context.user_data.get('awaiting_interface_lang'):
        if await handle_interface_language_choice(update, context):
            return

    # Priority 2: Interface language button pressed
    if choice == get_text(lang, 'btn_interface_language'):
        context.user_data['awaiting_interface_lang'] = True
        await update.message.reply_text(
            get_text(lang, 'choose_interface_language'),
            reply_markup=get_interface_language_keyboard()
        )
        return

    # Priority 3: Multi-language selection mode
    if context.user_data.get('lang_confirm_state'):
        if choice == get_text(lang, 'btn_confirm'):
            await _handle_confirm_choice(update, context, lang, supported_langs)
            return
        if await _handle_multi_lang_selection(update, context, lang, choice, supported_langs):
            return

    # Priority 4: Single language or menu buttons
    if await _handle_single_lang_choice(update, context, lang, choice, supported_langs):
        return

    if await _handle_menu_buttons(update, context, lang, choice):
        return

    # Nothing matched - show appropriate keyboard based on state
    await _show_fallback_keyboard(update, context, lang)


async def handle_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the information request.

    :param update: Update object
    :param context: Context object
    """
    lang = get_user_lang(context)
    await update.message.reply_text(
        get_text(lang, 'info_message'),
        reply_markup=get_main_keyboard(context)
    )
