import json
import os
import logging
from consts import REQUIRED_LANGUAGES, REQUIRED_KEYS

TRANSLATIONS_FILE = os.path.join(os.path.dirname(__file__), 'translations.json')
logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """
    Custom exception for translation-related errors.

    Raised when translations file is missing, invalid, or incomplete.
    Should be caught at application entry point for graceful shutdown.
    """


def load_translations() -> dict:
    """
    Load translations from JSON file with validation.
    Raises TranslationError if the file is missing or invalid.

    :return: Dictionary with translations
    :raises TranslationError: If translations file is missing, invalid, or incomplete
    """
    logger.debug('Loading translations from %s', TRANSLATIONS_FILE)

    if not os.path.exists(TRANSLATIONS_FILE):
        error_msg = f"Translations file '{TRANSLATIONS_FILE}' not found"
        logger.critical(error_msg)
        raise TranslationError(error_msg)

    try:
        with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        logger.debug('Translations file parsed successfully')
    except json.JSONDecodeError as e:
        error_msg = f'Translations file has invalid JSON format: {e}'
        logger.critical(error_msg)
        raise TranslationError(error_msg) from e
    except (OSError, IOError) as e:
        error_msg = f'Could not read translations file: {e}'
        logger.critical(error_msg)
        raise TranslationError(error_msg) from e

    if not isinstance(translations, dict):
        error_msg = 'Translations file must be a JSON object'
        logger.critical(error_msg)
        raise TranslationError(error_msg)

    # Validate required languages and keys
    for lang in REQUIRED_LANGUAGES:
        if lang not in translations:
            error_msg = f"Missing language '{lang}' in translations file"
            logger.critical(error_msg)
            raise TranslationError(error_msg)

        missing_keys = [key for key in REQUIRED_KEYS if key not in translations[lang]]
        if missing_keys:
            error_msg = f"Missing keys for language '{lang}': {missing_keys}"
            logger.critical(error_msg)
            raise TranslationError(error_msg)

        if not isinstance(translations[lang].get('ocr_languages'), dict):
            error_msg = f"'ocr_languages' for language '{lang}' must be an object"
            logger.critical(error_msg)
            raise TranslationError(error_msg)

        logger.debug("Language '%s' validated: %d keys found", lang, len(translations[lang]))

    logger.info('Translations loaded successfully: %d languages, %d required keys per language',
                len(REQUIRED_LANGUAGES), len(REQUIRED_KEYS))
    return translations


def get_text(lang_code: str, key: str, **kwargs) -> str:
    """
    Get localized text by key

    :param lang_code: Language code ('uk' or 'en')
    :param key: Translation key
    :param kwargs: Format arguments for the string
    :return: Localized string
    """
    text = TRANSLATIONS.get(lang_code, TRANSLATIONS['uk']).get(key, key)
    if text == key:
        logger.warning("Translation key '%s' not found for language '%s'", key, lang_code)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError as e:
            logger.error("Missing format argument %s for key '%s'", e, key)
    return text


def get_supported_languages(lang_code: str) -> dict:
    """
    Get supported OCR languages for the given interface language

    :param lang_code: Language code ('uk' or 'en')
    :return: Dictionary of language names to OCR codes
    """
    return TRANSLATIONS.get(lang_code, TRANSLATIONS['uk']).get('ocr_languages', {})


def get_all_translations_for_key(key: str) -> set:
    """
    Get all translations for a given key across all languages.
    Useful for creating dynamic filters without hardcoded strings.

    :param key: Translation key
    :return: Set of all translations for this key
    """
    translations_set = set()
    for lang_data in TRANSLATIONS.values():
        if key in lang_data:
            translations_set.add(lang_data[key])
    return translations_set


TRANSLATIONS = load_translations()
