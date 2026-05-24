import i18next from 'i18next';
import Backend from 'i18next-fs-backend';
import path from 'path';

export const initI18n = async () => {
  await i18next
    .use(Backend)
    .init({
      fallbackLng: 'en',
      preload: ['en', 'ru'],
      ns: ['common'],
      defaultNS: 'common',
      backend: {
        loadPath: path.join(__dirname, '../../locales/{{lng}}/{{ns}}.json'),
      },
      interpolation: {
        escapeValue: false,
      },
    });
};

export const t = (key: string, lng: string = 'en', options?: any): string => {
  return i18next.t(key, { ...options, lng }) as string;
};
