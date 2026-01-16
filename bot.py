import os
import shutil
import tempfile
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from reader import process_input_files, save_texts_to_files
from consts import ALLOWED_FORMATS, MAX_SIZE, DEFAULT_INTERFACE_LANG
from localization import get_text, get_supported_languages

ALPHABET_CHOICE = {}
FILE_PATHS = {}
LANG_SELECTION = {}
LANG_CONFIRM_STATE = {}
USER_INTERFACE_LANG = {}
AWAITING_INTERFACE_LANG = {}
USER_TEMP_DIRS = {}


def get_user_lang(user_id: int) -> str:
    """
    Get user's interface language

    :param user_id: User ID
    :return: Language code ('uk' or 'en')
    """
    return USER_INTERFACE_LANG.get(user_id, DEFAULT_INTERFACE_LANG)


def get_interface_language_keyboard():
    """
    Function to create a keyboard for interface language selection

    :return: ReplyKeyboardMarkup - keyboard with buttons
    """
    keyboard = [[KeyboardButton('Українська 🇺🇦'), KeyboardButton('English 🇬🇧')]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_main_keyboard(user_id: int):
    """
    Function to create a keyboard with language options

    :param user_id: User ID for localization
    :return: ReplyKeyboardMarkup: Keyboard with buttons
    """
    lang = get_user_lang(user_id)
    keyboard = [
        [KeyboardButton(get_text(lang, 'btn_ukrainian')), KeyboardButton(get_text(lang, 'btn_english')),
         KeyboardButton(get_text(lang, 'btn_other_language'))],
        [KeyboardButton(get_text(lang, 'btn_multiple_languages'))],
        [KeyboardButton(get_text(lang, 'btn_info')), KeyboardButton(get_text(lang, 'btn_interface_language'))]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_text_delivery_keyboard(user_id: int):
    """
    Function to create a keyboard with text delivery options

    :param user_id: User ID for localization
    :return: ReplyKeyboardMarkup: Keyboard with buttons
    """
    lang = get_user_lang(user_id)
    keyboard = [[KeyboardButton(get_text(lang, 'btn_message')), KeyboardButton(get_text(lang,
                                                                                        'btn_text_file'))]]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_language_keyboard(user_id: int):
    """
    Function to create a keyboard with all supported languages and a return button

    :param user_id: User ID for localization
    :return: ReplyKeyboardMarkup - keyboard with buttons
    """
    lang = get_user_lang(user_id)
    supported_langs = get_supported_languages(lang)

    keyboard = [[KeyboardButton(get_text(lang, 'btn_back_to_menu'))]]
    if LANG_CONFIRM_STATE.get(user_id):
        keyboard.insert(0, [KeyboardButton(get_text(lang, 'btn_confirm'))])
    keyboard.extend([[KeyboardButton(lang_name)] for lang_name in supported_langs.keys()])
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Function to handle the /start command - shows interface language selection first

    :param update: Update object
    :param context: Context object
    """
    user_id = update.effective_user.id
    AWAITING_INTERFACE_LANG[user_id] = True
    await update.message.reply_text(
        get_text('uk', 'choose_interface_language'),
        reply_markup=get_interface_language_keyboard()
    )


async def handle_interface_language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Function to handle interface language selection

    :param update: Update object
    :param context: Context object
    """
    user_id = update.effective_user.id
    choice = update.message.text

    if not AWAITING_INTERFACE_LANG.get(user_id):
        return False

    if choice == 'Українська 🇺🇦':
        USER_INTERFACE_LANG[user_id] = 'uk'
    elif choice == 'English 🇬🇧':
        USER_INTERFACE_LANG[user_id] = 'en'
    else:
        return False

    AWAITING_INTERFACE_LANG[user_id] = False
    lang = get_user_lang(user_id)
    await update.message.reply_text(get_text(lang, 'interface_language_set'),
                                    reply_markup=get_main_keyboard(user_id))
    await update.message.reply_text(get_text(lang, 'start_message'), reply_markup=get_main_keyboard(user_id))
    return True


async def _handle_confirm_choice(update: Update, user_id: int, lang: str, supported_langs: dict) -> bool:
    """
    Function to handle confirm button in multi-language selection mode.

    :param update: Update object
    :param user_id: User ID
    :param lang: User's interface language
    :param supported_langs: Dictionary of supported languages
    :return: True if handled, False otherwise
    """
    LANG_CONFIRM_STATE[user_id] = False
    if LANG_SELECTION[user_id]:
        final_lang_string = '+'.join(LANG_SELECTION[user_id])
        ALPHABET_CHOICE[user_id] = final_lang_string
        lang_names = [k for k, v in supported_langs.items() if v in LANG_SELECTION[user_id]]
        await update.message.reply_text(get_text(lang, 'selected_languages', langs=str(lang_names)))
    else:
        await update.message.reply_text(get_text(lang, 'no_language_selected'))
    return True


async def _handle_multi_lang_selection(update: Update, user_id: int, lang: str,
                                       choice: str, supported_langs: dict) -> bool:
    """
    Function to handle language selection in multi-language mode.

    :param update: Update object
    :param user_id: User ID
    :param lang: User's interface language
    :param choice: User's choice
    :param supported_langs: Dictionary of supported languages
    :return: True if handled, False otherwise
    """
    choice_lower = choice.lower()
    if choice_lower in supported_langs:
        ocr_code = supported_langs[choice_lower]
        if ocr_code not in LANG_SELECTION[user_id]:
            LANG_SELECTION[user_id].append(ocr_code)

        await update.message.reply_text(
            get_text(lang, 'language_added', lang=choice),
            reply_markup=get_language_keyboard(user_id)
        )
        return True

    return False


async def _handle_single_lang_choice(update: Update, user_id: int, lang: str,
                                     choice: str, supported_langs: dict) -> bool:
    """
    Function to handle single language selection.
    :param update: Update object
    :param user_id: User ID
    :param lang: User's interface language
    :param choice: User's choice
    :param supported_langs: Dictionary of supported languages
    :return: True if handled, False otherwise
    """
    choice_lower = choice.lower()
    lang_map = {
        get_text(lang, 'btn_ukrainian'): 'ukr',
        get_text(lang, 'btn_english'): 'eng',
    }

    if choice in lang_map:
        ALPHABET_CHOICE[user_id] = lang_map[choice]
        await update.message.reply_text(get_text(lang, 'language_selected', lang=choice))
        return True

    if choice_lower in supported_langs:
        ALPHABET_CHOICE[user_id] = supported_langs[choice_lower]
        await update.message.reply_text(get_text(lang, 'language_selected', lang=choice))
        return True

    return False


async def _handle_menu_buttons(update: Update, user_id: int, lang: str, choice: str) -> bool:
    """
    Function to handle menu navigation buttons.

    :param update: Update object
    :param user_id: User ID
    :param lang: User's interface language
    :param choice: User's choice
    :return: True if handled, False otherwise
    """
    if choice == get_text(lang, 'btn_other_language'):
        await update.message.reply_text(
            get_text(lang, 'choose_language'),
            reply_markup=get_language_keyboard(user_id)
        )
        return True

    if choice == get_text(lang, 'btn_multiple_languages'):
        LANG_CONFIRM_STATE[user_id] = True
        LANG_SELECTION[user_id] = []
        await update.message.reply_text(
            get_text(lang, 'choose_multiple_languages'),
            reply_markup=get_language_keyboard(user_id)
        )
        return True

    if choice == get_text(lang, 'btn_back_to_menu'):
        LANG_CONFIRM_STATE[user_id] = False
        await update.message.reply_text(
            get_text(lang, 'choose_alphabet'),
            reply_markup=get_main_keyboard(user_id)
        )
        return True

    return False


async def handle_alphabet_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Function to handle the choice of alphabet

    :param update: - update object
    :param context: - context object
    """
    user_id = update.effective_user.id
    choice = update.message.text
    lang = get_user_lang(user_id)
    supported_langs = get_supported_languages(lang)

    if AWAITING_INTERFACE_LANG.get(user_id):
        if await handle_interface_language_choice(update, context):
            return

    if choice == get_text(lang, 'btn_interface_language'):
        AWAITING_INTERFACE_LANG[user_id] = True
        await update.message.reply_text(
            get_text(lang, 'choose_interface_language'),
            reply_markup=get_interface_language_keyboard()
        )
        return

    if LANG_CONFIRM_STATE.get(user_id):
        if choice == get_text(lang, 'btn_confirm'):
            await _handle_confirm_choice(update, user_id, lang, supported_langs)
            return
        if await _handle_multi_lang_selection(update, user_id, lang, choice, supported_langs):
            return

    if await _handle_single_lang_choice(update, user_id, lang, choice, supported_langs):
        return

    if await _handle_menu_buttons(update, user_id, lang, choice):
        return

    await update.message.reply_text(
        get_text(lang, 'please_choose_alphabet'),
        reply_markup=get_main_keyboard(user_id)
    )


async def handle_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Function to handle the information request

    :param update: - update object
    :param context: - context object
    """
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    await update.message.reply_text(
        get_text(lang, 'info_message'),
        reply_markup=get_main_keyboard(user_id)
    )


async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Function to handle file uploads

    :param update: - update object
    :param context: - context object
    """
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    if not update.message.document:
        await update.message.reply_text(get_text(lang, 'not_document'))
        return

    doc = update.message.document
    if doc.file_size > MAX_SIZE:
        await update.message.reply_text(get_text(lang, 'file_too_large', filename=doc.file_name))
        return

    ext = os.path.splitext(doc.file_name)[1].lower().replace('.', '')
    if ext not in ALLOWED_FORMATS:
        await update.message.reply_text(get_text(lang, 'unsupported_format', filename=doc.file_name))
        return

    if user_id not in USER_TEMP_DIRS:
        USER_TEMP_DIRS[user_id] = tempfile.mkdtemp(prefix=f'ocr_bot_{user_id}_')

    temp_dir = USER_TEMP_DIRS[user_id]
    download_path = os.path.join(temp_dir, doc.file_name)
    file = await doc.get_file()
    await file.download_to_drive(custom_path=download_path)

    FILE_PATHS[user_id] = [] if user_id not in FILE_PATHS else FILE_PATHS[user_id]
    FILE_PATHS[user_id].append(download_path)

    if len(FILE_PATHS[user_id]) == 1:
        await update.message.reply_text(
            get_text(lang, 'file_uploaded'),
            reply_markup=get_text_delivery_keyboard(user_id)
        )


async def _send_as_messages(update: Update, texts_dict: dict, output_dir: str, lang: str):
    """
    Send OCR results as text messages.

    :param update: Update object
    :param texts_dict: Dictionary with file names and extracted text
    :param output_dir: Directory where text files are saved
    :param lang: User's interface language
    """
    for file_name in texts_dict:
        output_file = os.path.join(output_dir, f'{os.path.splitext(file_name)[0]}.txt')
        with open(output_file, 'r', encoding='utf-8') as f:
            text = f.read()
        await update.message.reply_text(get_text(lang, 'file_header', filename=file_name))
        await update.message.reply_text(text)


async def _send_as_files(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         texts_dict: dict, output_dir: str):
    """
    Function to send OCR results as text files.

    :param update: Update object
    :param context: Context object
    :param texts_dict: Dictionary with file names and extracted text
    :param output_dir: Directory where text files are saved
    """
    for file_name in texts_dict:
        output_file = os.path.join(output_dir, f'{os.path.splitext(file_name)[0]}.txt')
        with open(output_file, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename=f'{os.path.splitext(file_name)[0]}.txt'
            )


def _cleanup_user_files(user_id: int):
    """
    Function to clean up temporary files for user.

    :param user_id: User ID
    """
    if user_id in USER_TEMP_DIRS:
        temp_dir = USER_TEMP_DIRS[user_id]
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        del USER_TEMP_DIRS[user_id]
    if user_id in FILE_PATHS:
        del FILE_PATHS[user_id]


async def handle_text_delivery_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Function to handle the choice of text delivery method

    :param update: - update object
    :param context: - context object
    """
    user_id = update.effective_user.id
    choice = update.message.text
    lang = get_user_lang(user_id)
    file_paths = FILE_PATHS.get(user_id)
    ocr_lang = ALPHABET_CHOICE.get(user_id, 'ukr')

    if not file_paths:
        await update.message.reply_text(get_text(lang, 'please_upload_file'))
        return

    try:
        texts_dict = process_input_files(file_paths, ocr_lang)

        with tempfile.TemporaryDirectory(prefix='ocr_output_') as output_dir:
            save_texts_to_files(texts_dict, output_dir)

            if choice == get_text(lang, 'btn_message'):
                await _send_as_messages(update, texts_dict, output_dir, lang)
            elif choice == get_text(lang, 'btn_text_file'):
                await _send_as_files(update, context, texts_dict, output_dir)
            else:
                await update.message.reply_text(get_text(lang, 'please_choose_delivery'))
                return
    finally:
        _cleanup_user_files(user_id)

    await update.message.reply_text(
        get_text(lang, 'choose_alphabet'),
        reply_markup=get_main_keyboard(user_id)
    )


if __name__ == '__main__':
    load_dotenv()
    app = ApplicationBuilder().token(os.getenv('TOKEN')).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex('(Інформація ℹ️|Information ℹ️)'),
        handle_info
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex('(Повідомлення|Текстовий файл|Message|Text file)'),
        handle_text_delivery_choice
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_alphabet_choice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_files))
    app.run_polling()
