import json
import os

class I18n:
    def __init__(self, locales_dir='locales'):
        self.locales_dir = locales_dir
        self.translations = {}
        self._load_translations()

    def _load_translations(self):
        for lang in ['en', 'ru']:
            file_path = os.path.join(self.locales_dir, lang, 'common.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)

    def get(self, key, lang='en', **kwargs):
        text = self.translations.get(lang, {}).get(key, key)
        for k, v in kwargs.items():
            text = text.replace(f'{{{{{k}}}}}', str(v))
        return text

i18n = I18n()
