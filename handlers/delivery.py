"""
Text delivery handlers and OCR processing.
"""
import os
import shutil
import logging
import asyncio
import tempfile

from telegram import Update
from telegram.constants import ChatAction
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from consts import TELEGRAM_MAX_MESSAGE_LENGTH, HEADER_RESERVE
from localization import get_text
from reader import process_input_files, save_texts_to_files
from utils.keyboards import get_user_lang, get_main_keyboard

logger = logging.getLogger(__name__)


def _split_text_into_chunks(text: str, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> list:
    """
    Split text into chunks that fit within Telegram's message size limit.
    Tries to split at newlines or spaces to avoid breaking words.

    :param text: Text to split
    :param max_length: Maximum length of each chunk
    :return: List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        split_point = max_length

        newline_pos = text.rfind('\n', 0, max_length)
        if newline_pos > max_length // 2:
            split_point = newline_pos + 1
        else:
            space_pos = text.rfind(' ', 0, max_length)
            if space_pos > max_length // 2:
                split_point = space_pos + 1

        chunks.append(text[:split_point])
        text = text[split_point:]

    return chunks


async def _send_as_messages(update: Update, texts_dict: dict, lang: str):
    """
    Send OCR results as text messages.
    Uses texts_dict directly without reading from files.
    Handles Telegram's 4096 character limit by splitting long texts.

    :param update: Update object
    :param texts_dict: Dictionary with file names and extracted text
    :param lang: User's interface language
    """
    for file_name, text in texts_dict.items():
        await update.message.reply_text(
            get_text(lang, 'file_header', filename=file_name)
        )

        if not text or not text.strip():
            await update.message.reply_text(get_text(lang, 'no_text_found'))
            continue

        # Check if text needs splitting
        if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
            await update.message.reply_text(text)
            continue

        # For multipart messages, reserve space for header
        effective_max_length = TELEGRAM_MAX_MESSAGE_LENGTH - HEADER_RESERVE
        chunks = _split_text_into_chunks(text, effective_max_length)

        for i, chunk in enumerate(chunks):
            part_header = get_text(lang, 'message_part', current=i + 1, total=len(chunks))
            await update.message.reply_text(f"{part_header}\n{chunk}")


async def _send_as_files(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        texts_dict: dict,
        output_dir: str,
        lang: str
):
    """
    Send OCR results as text files.

    :param update: Update object
    :param context: Context object
    :param texts_dict: Dictionary with file names and extracted text
    :param output_dir: Directory where text files are saved
    :param lang: User's interface language
    """
    for file_name in texts_dict:
        output_file = os.path.join(output_dir, f'{os.path.splitext(file_name)[0]}.txt')
        try:
            with open(output_file, 'rb') as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    filename=f'{os.path.splitext(file_name)[0]}.txt'
                )
        except IOError as e:
            logger.error('Error reading file %s: %s', output_file, e)
            await update.message.reply_text(
                get_text(lang, 'file_read_error', filename=file_name)
            )


def _cleanup_user_files(context: ContextTypes.DEFAULT_TYPE):
    """
    Clean up temporary files for user.

    :param context: Context object
    """
    temp_dir = context.user_data.get('temp_dir')
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    context.user_data.pop('temp_dir', None)
    context.user_data.pop('file_paths', None)
    context.user_data.pop('delivery_choice', None)
    context.user_data.pop('awaiting_delivery_choice', None)


async def _process_ocr_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Process OCR on uploaded files and send results.
    OCR processing runs in a separate thread to keep the bot responsive.

    :param update: Update object
    :param context: Context object
    """
    user_id = update.effective_user.id
    lang = get_user_lang(context)
    file_paths = context.user_data.get('file_paths', [])
    ocr_lang = context.user_data.get('ocr_lang_choice', 'ukr')
    delivery_choice = context.user_data.get('delivery_choice', 'message')

    if not file_paths:
        logger.warning('User %s tried to process without uploading files', user_id)
        await update.message.reply_text(get_text(lang, 'please_upload_file'))
        return

    try:
        # Notify user that processing has started
        await update.message.reply_text(get_text(lang, 'processing_started'))

        # Send typing action
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING
        )

        logger.info('User %s started OCR processing with language: %s', user_id, ocr_lang)

        # Run OCR in separate thread
        texts_dict = await asyncio.to_thread(process_input_files, file_paths, ocr_lang)

        logger.info('User %s OCR completed for %s file(s)', user_id, len(texts_dict))

        # Validate results
        if not texts_dict or all(not (text or '').strip() for text in texts_dict.values()):
            logger.warning('User %s OCR produced no text', user_id)
            await update.message.reply_text(get_text(lang, 'no_text_extracted'))
            return

        if delivery_choice == 'message':
            logger.info('User %s sending results as messages', user_id)
            await _send_as_messages(update, texts_dict, lang)
        else:
            with tempfile.TemporaryDirectory(prefix='ocr_output_') as output_dir:
                await asyncio.to_thread(save_texts_to_files, texts_dict, output_dir)
                logger.info('User %s sending results as files', user_id)
                await _send_as_files(update, context, texts_dict, output_dir, lang)

    except TelegramError as e:
        logger.error('User %s Telegram error: %s', user_id, e, exc_info=True)
        await update.message.reply_text(get_text(lang, 'processing_error'))
    except (OSError, IOError) as e:
        logger.error('User %s file I/O error: %s', user_id, e, exc_info=True)
        await update.message.reply_text(get_text(lang, 'processing_error'))
    except (ValueError, RuntimeError) as e:
        logger.error('User %s OCR processing error: %s', user_id, e, exc_info=True)
        await update.message.reply_text(get_text(lang, 'processing_error'))
    finally:
        _cleanup_user_files(context)

    await update.message.reply_text(
        get_text(lang, 'choose_alphabet'),
        reply_markup=get_main_keyboard(context)
    )


async def handle_text_delivery_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the choice of text delivery method.
    Runs OCR and sends results based on selected delivery method.

    :param update: Update object
    :param context: Context object
    """
    user_id = update.effective_user.id
    choice = update.message.text
    lang = get_user_lang(context)
    file_paths = context.user_data.get('file_paths')

    if not file_paths:
        logger.warning('User %s tried to process without uploading files', user_id)
        await update.message.reply_text(get_text(lang, 'please_upload_file'))
        return

    if choice == get_text(lang, 'btn_message'):
        context.user_data['delivery_choice'] = 'message'
        context.user_data['awaiting_delivery_choice'] = False
        logger.info('User %s selected delivery method: message', user_id)
    elif choice == get_text(lang, 'btn_text_file'):
        context.user_data['delivery_choice'] = 'file'
        context.user_data['awaiting_delivery_choice'] = False
        logger.info('User %s selected delivery method: file', user_id)
    else:
        await update.message.reply_text(get_text(lang, 'please_choose_delivery'))
        return

    await _process_ocr_and_send(update, context)
