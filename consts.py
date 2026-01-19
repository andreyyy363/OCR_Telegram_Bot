ALLOWED_FORMATS = ('pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif')
MAX_SIZE = 10 * 1024 * 1024
DEFAULT_INTERFACE_LANG = 'uk'
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
HEADER_RESERVE = 25

# Logging settings
LOG_DIR_NAME = 'logs'
LOG_FILE_NAME = 'bot.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5
LOG_ENCODING = 'utf-8'

REQUIRED_LANGUAGES = ['uk', 'en']
REQUIRED_KEYS = [
    'btn_ukrainian', 'btn_english', 'btn_other_language', 'btn_multiple_languages',
    'btn_info', 'btn_interface_language', 'btn_back_to_menu', 'btn_confirm',
    'btn_message', 'btn_text_file', 'choose_interface_language', 'interface_language_set',
    'start_message', 'info_message', 'choose_alphabet', 'choose_language',
    'language_selected', 'selected_languages', 'no_language_selected', 'language_added',
    'choose_multiple_languages', 'please_choose_alphabet', 'not_document', 'file_too_large',
    'unsupported_format', 'file_uploaded', 'please_upload_file', 'please_choose_delivery',
    'file_header', 'no_text_found', 'message_part', 'file_read_error',
    'processing_started', 'processing_error', 'no_text_extracted', 'ocr_languages'
]
