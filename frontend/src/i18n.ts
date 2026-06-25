export type Locale = "ru" | "en";

const MESSAGES: Record<Locale, Record<string, string>> = {
  ru: {
    "tab.feed": "Лента",
    "tab.cooks": "Повара",
    "tab.orders": "Заказы",
    "tab.favorites": "Избранное",
    "tab.kitchen": "Кухня",
    "tab.profile": "Профиль",
    "onboarding.title": "Как пользоваться",
    "onboarding.step1": "Геолокация — блюда рядом",
    "onboarding.step2": "Поиск — название или категория",
    "onboarding.step3": "Заказ или запрос поварам",
    "onboarding.geo": "Включить гео",
    "onboarding.done": "Понятно",
    "profile.title": "Профиль",
    "profile.language": "Язык",
    "profile.lang.ru": "Русский",
    "profile.lang.en": "English",
    "app.error": "Откройте приложение через Telegram",
    "app.hint": "Запустите бота и нажмите «Открыть Еда Рядом».",
    "feed.orders": "Заказы",
    "feed.wish": "Запрос поварам",
    "feed.no_geo": "Включите геолокацию в шапке",
    "feed.no_supply": "Нет блюд в каталоге",
    "feed.search_placeholder": "Что хотите поесть?",
  },
  en: {
    "tab.feed": "Feed",
    "tab.cooks": "Cooks",
    "tab.orders": "Orders",
    "tab.favorites": "Favorites",
    "tab.kitchen": "Kitchen",
    "tab.profile": "Profile",
    "onboarding.title": "Quick start",
    "onboarding.step1": "Location — dishes nearby",
    "onboarding.step2": "Search — dish or category",
    "onboarding.step3": "Order or request a cook",
    "onboarding.geo": "Enable location",
    "onboarding.done": "Got it",
    "profile.title": "Profile",
    "profile.language": "Language",
    "profile.lang.ru": "Русский",
    "profile.lang.en": "English",
    "app.error": "Open the app from Telegram",
    "app.hint": "Start the bot and tap «Open Food Nearby».",
    "feed.orders": "Orders",
    "feed.wish": "Request cooks",
    "feed.no_geo": "Enable location in the header",
    "feed.no_supply": "No dishes in catalog",
    "feed.search_placeholder": "What would you like to eat?",
  },
};

let currentLocale: Locale = "ru";

export function setLocale(locale: string | null | undefined): void {
  const base = (locale ?? "ru").split("-")[0].toLowerCase();
  currentLocale = base === "en" ? "en" : "ru";
}

export function getLocale(): Locale {
  return currentLocale;
}

export function t(key: string): string {
  return MESSAGES[currentLocale][key] ?? MESSAGES.ru[key] ?? key;
}

export function detectTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export const TAB_KEYS = [
  { cookOnly: false, end: true, icon: "feed" as const, labelKey: "tab.feed", to: "/" },
  { cookOnly: false, end: false, icon: "cooks" as const, labelKey: "tab.cooks", to: "/cooks" },
  { cookOnly: false, end: false, icon: "orders" as const, labelKey: "tab.orders", to: "/orders" },
  { cookOnly: false, end: false, icon: "favorites" as const, labelKey: "tab.favorites", to: "/favorites" },
  { cookOnly: true, end: false, icon: "kitchen" as const, labelKey: "tab.kitchen", to: "/my-kitchen" },
  { cookOnly: false, end: false, icon: "profile" as const, labelKey: "tab.profile", to: "/profile" },
];
