"""
File upload handler.
"""
import os
import logging
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from consts import ALLOWED_FORMATS, MAX_SIZE
from localization import get_text
from utils.keyboards import get_user_lang, get_text_delivery_keyboard
from utils.helpers import sanitize_filename

logger = logging.getLogger(__name__)


async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle file uploads.

    :param update: Update object
    :param context: Context object
    """
    user_id = update.effective_user.id
    lang = get_user_lang(context)

    if not update.message.document:
        await update.message.reply_text(get_text(lang, 'not_document'))
        return

    doc = update.message.document

    # Check file size
    if doc.file_size > MAX_SIZE:
        logger.warning(
            'User %s uploaded file too large: %s (%s bytes)',
            user_id, doc.file_name, doc.file_size
        )
        await update.message.reply_text(
            get_text(lang, 'file_too_large', filename=doc.file_name)
        )
        return

    # Check file format
    ext = os.path.splitext(doc.file_name)[1].lower().replace('.', '')
    if ext not in ALLOWED_FORMATS:
        logger.warning('User %s uploaded unsupported format: %s', user_id, doc.file_name)
        await update.message.reply_text(
            get_text(lang, 'unsupported_format', filename=doc.file_name)
        )
        return

    # Create temp directory if not exists
    if 'temp_dir' not in context.user_data:
        context.user_data['temp_dir'] = tempfile.mkdtemp(prefix=f'ocr_bot_{user_id}_')

    temp_dir = context.user_data['temp_dir']

    # Sanitize filename to prevent path traversal
    safe_name = sanitize_filename(doc.file_name)
    download_path = os.path.join(temp_dir, safe_name)

    # Ensure uniqueness if file with same name exists
    base, ext_with_dot = os.path.splitext(safe_name)
    counter = 1
    while os.path.exists(download_path):
        download_path = os.path.join(temp_dir, f"{base}_{counter}{ext_with_dot}")
        counter += 1

    # Download file
    file = await doc.get_file()
    await file.download_to_drive(custom_path=download_path)

    # Store file path
    file_paths = context.user_data.get('file_paths', [])
    file_paths.append(download_path)
    context.user_data['file_paths'] = file_paths
    logger.info('User %s uploaded file: %s', user_id, doc.file_name)

    # Show delivery choice keyboard after first file
    if len(file_paths) == 1:
        context.user_data['awaiting_delivery_choice'] = True
        await update.message.reply_text(
            get_text(lang, 'file_uploaded'),
            reply_markup=get_text_delivery_keyboard(context)
        )
