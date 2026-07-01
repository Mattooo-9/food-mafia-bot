const FALLBACK_RU: Record<string, string> = {
  "tab.feed": "Лента",
  "tab.cooks": "Повара",
  "tab.orders": "Заказы",
  "tab.favorites": "Избранное",
  "tab.kitchen": "Кухня",
  "tab.profile": "Профиль",
  "app.title": "Еда Рядом",
  "app.error": "Откройте приложение через Telegram",
  "app.hint": "Запустите бота и нажмите «Открыть Еда Рядом».",
  "search.placeholder": "Что хотите поесть?",
  "geo.enable": "Гео",
  "geo.nearby": "Рядом",
  "geo.nearby_section": "Рядом",
  "search.not_found": "Не найдено",
  "feed.no_geo": "Включите «Гео» в шапке",
  "feed.no_supply": "Рядом пока пусто",
  "profile.title": "Профиль",
  "orders.title": "Заказы",
};

const FALLBACK_EN: Record<string, string> = {
  "tab.feed": "Feed",
  "tab.cooks": "Cooks",
  "tab.orders": "Orders",
  "tab.favorites": "Saved",
  "tab.kitchen": "Kitchen",
  "tab.profile": "Profile",
  "app.title": "Food Nearby",
  "app.error": "Open the app from Telegram",
  "app.hint": "Start the bot and open the mini app.",
  "search.placeholder": "What would you like?",
  "geo.enable": "Geo",
  "geo.nearby": "Nearby",
  "geo.nearby_section": "Nearby",
  "search.not_found": "Not found",
  "feed.no_geo": "Turn on Geo in the header",
  "feed.no_supply": "Nothing nearby yet",
  "profile.title": "Profile",
  "orders.title": "Orders",
};

let strings: Record<string, string> = { ...FALLBACK_RU };
let currentLocale = "ru";

export function applyBundle(locale: string, bundle: Record<string, string>): void {
  const base = (locale || "en").split("-")[0].toLowerCase();
  currentLocale = base;
  const fallback = base === "ru" ? FALLBACK_RU : FALLBACK_EN;
  strings = { ...fallback, ...bundle };
}

export function setLocale(locale: string | null | undefined): void {
  const base = (locale ?? "en").split("-")[0].toLowerCase();
  currentLocale = base;
  strings = base === "ru" ? { ...FALLBACK_RU } : { ...FALLBACK_EN };
}

export function getLocale(): string {
  return currentLocale;
}

export function t(key: string): string {
  return strings[key] ?? FALLBACK_EN[key] ?? FALLBACK_RU[key] ?? key;
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
