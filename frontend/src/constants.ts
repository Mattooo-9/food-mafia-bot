import type { IconName } from "./components/icons";
import type { FeedType, OrderStatus, PaymentMethod, PaymentStatus } from "./types";

/** Способы оплаты — по алфавиту (ru). */
export const PAYMENT_METHODS: { id: PaymentMethod; label: string }[] = [
  { id: "STARS" as PaymentMethod, label: "Telegram Stars ⭐" },
  { id: "TON" as PaymentMethod, label: "TON 💎" },
].sort((a, b) => a.label.localeCompare(b.label, "ru"));

export const PAYMENT_METHOD_LABELS: Record<string, string> = {
  STARS: "Telegram Stars",
  TON: "TON",
  CARD: "Картой при получении",
  CASH: "Наличные",
  TRANSFER: "Перевод",
};

export const PAYMENT_STATUS_LABELS: Record<PaymentStatus, string> = {
  PAID: "Оплачено",
  PENDING: "Ожидает оплаты",
};

/** Ленты — по алфавиту (ru). */
export const FEEDS: { id: FeedType; label: string }[] = [
  { id: "fast", label: "⚡ Быстрые" },
  { id: "cheap", label: "💸 Дешёвое" },
  { id: "new", label: "🆕 Новые" },
  { id: "popular", label: "🔥 Популярное" },
  { id: "nearby", label: "📍 Рядом" },
];

/** Фильтры расстояния — по алфавиту подписи (ru). */
export const DISTANCES: { label: string; value: number | null }[] = [
  { label: "1 км", value: 1000 },
  { label: "10 км", value: 10000 },
  { label: "3 км", value: 3000 },
  { label: "500 м", value: 500 },
  { label: "5 км", value: 5000 },
  { label: "Любое расстояние", value: null },
];

/** Фильтры рейтинга — по алфавиту подписи (ru). */
export const RATINGS: { label: string; value: number | null }[] = [
  { label: "3+", value: 3 },
  { label: "4+", value: 4 },
  { label: "4.5+", value: 4.5 },
  { label: "Любой рейтинг", value: null },
];

export const WISH_STATUS_LABELS: Record<string, string> = {
  OPEN: "ищем повара",
  CLAIMED: "повар взял",
  COMPLETED: "выполнен",
  CANCELLED: "отменён",
};

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  ACCEPTED: "Принят",
  CANCELLED: "Отменён",
  COOKING: "Готовится",
  DELIVERED: "Доставлен",
  NEW: "Новый",
  READY: "Готов",
};

/** Приоритет статуса для сортировки (активные выше). */
export const ORDER_STATUS_RANK: Record<OrderStatus, number> = {
  ACCEPTED: 2,
  CANCELLED: 99,
  COOKING: 3,
  DELIVERED: 90,
  NEW: 1,
  READY: 4,
};

/** Действия повара по статусу — подписи по алфавиту (ru). */
export const COOK_ORDER_ACTIONS: Partial<
  Record<OrderStatus, { label: string; status: OrderStatus }[]>
> = {
  ACCEPTED: [
    { label: "Готовлю", status: "COOKING" as OrderStatus },
    { label: "Отменить", status: "CANCELLED" as OrderStatus },
  ].sort((a, b) => a.label.localeCompare(b.label, "ru")),
  COOKING: [{ label: "Готово", status: "READY" as OrderStatus }],
  NEW: [
    { label: "Отклонить", status: "CANCELLED" as OrderStatus },
    { label: "Принять", status: "ACCEPTED" as OrderStatus },
  ].sort((a, b) => a.label.localeCompare(b.label, "ru")),
  READY: [{ label: "Выдан", status: "DELIVERED" as OrderStatus }],
};

/** Вкладки кухни */
export const KITCHEN_TABS = [
  { id: "orders" as const, label: "Заказы" },
  { id: "wishes" as const, label: "Запросы" },
  { id: "foods" as const, label: "Блюда" },
];

/** Вкладки — лента первая (главная). */
export const TABS: {
  cookOnly: boolean;
  end: boolean;
  icon: IconName;
  label: string;
  to: string;
}[] = [
  { cookOnly: false, end: true, icon: "feed", label: "Лента", to: "/" },
  { cookOnly: false, end: false, icon: "cooks", label: "Повара", to: "/cooks" },
  { cookOnly: false, end: false, icon: "orders", label: "Заказы", to: "/orders" },
  { cookOnly: false, end: false, icon: "favorites", label: "Избранное", to: "/favorites" },
  { cookOnly: true, end: false, icon: "kitchen", label: "Кухня", to: "/my-kitchen" },
  { cookOnly: false, end: false, icon: "profile", label: "Профиль", to: "/profile" },
];

export function sortRu(values: string[]): string[] {
  return [...values].sort((a, b) => {
    if (a === "Другое") return 1;
    if (b === "Другое") return -1;
    return a.localeCompare(b, "ru");
  });
}
