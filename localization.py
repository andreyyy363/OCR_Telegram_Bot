import json
import sys
import os

TRANSLATIONS_FILE = os.path.join(os.path.dirname(__file__), 'translations.json')

REQUIRED_KEYS = [
    'btn_ukrainian', 'btn_english', 'btn_other_language', 'btn_multiple_languages',
    'btn_info', 'btn_interface_language', 'btn_back_to_menu', 'btn_confirm',
    'btn_message', 'btn_text_file', 'choose_interface_language', 'interface_language_set',
    'start_message', 'info_message', 'choose_alphabet', 'choose_language',
    'language_selected', 'selected_languages', 'no_language_selected', 'language_added',
    'choose_multiple_languages', 'please_choose_alphabet', 'not_document', 'file_too_large',
    'unsupported_format', 'file_uploaded', 'please_upload_file', 'please_choose_delivery',
    'file_header', 'ocr_languages'
]

REQUIRED_LANGUAGES = ['uk', 'en']


def load_translations() -> dict:
    """
    Load translations from JSON file with validation.
    Exits the program if the file is missing or invalid.

    :return: Dictionary with translations
    """
    if not os.path.exists(TRANSLATIONS_FILE):
        print(f"ПОМИЛКА: Файл перекладів '{TRANSLATIONS_FILE}' не знайдено!")
        print('ERROR: Translations file not found!')
        sys.exit(1)

    try:
        with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
            translations = json.load(f)
    except json.JSONDecodeError as e:
        print('ПОМИЛКА: Файл перекладів має некоректний JSON формат!')
        print('ERROR: Translations file has invalid JSON format!')
        print(f'Деталі / Details: {e}')
        sys.exit(1)
    except (OSError, IOError) as e:
        print('ПОМИЛКА: Не вдалося прочитати файл перекладів!')
        print('ERROR: Could not read translations file!')
        print(f'Деталі / Details: {e}')
        sys.exit(1)

    if not isinstance(translations, dict):
        print("ПОМИЛКА: Файл перекладів має бути JSON об'єктом!")
        print('ERROR: Translations file must be a JSON object!')
        sys.exit(1)

    for lang in REQUIRED_LANGUAGES:
        if lang not in translations:
            print(f"ПОМИЛКА: Відсутня мова '{lang}' у файлі перекладів!")
            print(f"ERROR: Missing language '{lang}' in translations file!")
            sys.exit(1)

        missing_keys = [key for key in REQUIRED_KEYS if key not in translations[lang]]
        if missing_keys:
            print(f"ПОМИЛКА: Відсутні ключі для мови '{lang}': {missing_keys}")
            print(f"ERROR: Missing keys for language '{lang}': {missing_keys}")
            sys.exit(1)

        if not isinstance(translations[lang].get('ocr_languages'), dict):
            print(f"ПОМИЛКА: 'ocr_languages' для мови '{lang}' має бути об'єктом!")
            print(f"ERROR: 'ocr_languages' for language '{lang}' must be an object!")
            sys.exit(1)

    print('Файл перекладів успішно завантажено / Translations file loaded successfully')
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
    if kwargs:
        text = text.format(**kwargs)
    return text


def get_supported_languages(lang_code: str) -> dict:
    """
    Get supported OCR languages for the given interface language

    :param lang_code: Language code ('uk' or 'en')
    :return: Dictionary of language names to OCR codes
    """
    return TRANSLATIONS.get(lang_code, TRANSLATIONS['uk']).get('ocr_languages', {})


TRANSLATIONS = load_translations()
