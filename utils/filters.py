"""
Custom message filters for the OCR Telegram Bot.
"""
from telegram.ext import filters
from localization import get_all_translations_for_key


def create_translation_filter(translation_key: str) -> filters.MessageFilter:
    """
    Create a dynamic filter that matches text against all translations of a given key.

    This eliminates hardcoded regex patterns and makes the bot maintainable
    when translations change or new languages are added.

    :param translation_key: The translation key (e.g., 'btn_info')
    :return: MessageFilter instance
    """
    valid_texts = get_all_translations_for_key(translation_key)

    class TranslationFilter(filters.MessageFilter):
        def filter(self, message):
            return message.text in valid_texts if message.text else False

    return TranslationFilter()


def create_multi_key_filter(*translation_keys: str) -> filters.MessageFilter:
    """
    Create a filter that matches text against translations of multiple keys.

    Useful when multiple buttons should trigger the same handler.

    :param translation_keys: Translation keys to match
    :return: MessageFilter instance
    """
    valid_texts = set()
    for key in translation_keys:
        valid_texts.update(get_all_translations_for_key(key))

    class MultiKeyFilter(filters.MessageFilter):
        def filter(self, message):
            return message.text in valid_texts if message.text else False

    return MultiKeyFilter()
