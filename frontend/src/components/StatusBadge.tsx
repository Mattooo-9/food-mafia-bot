import type { OrderStatus } from "../types";

const LABELS: Record<OrderStatus, string> = {
  NEW: "Новый",
  ACCEPTED: "Принят",
  COOKING: "Готовится",
  READY: "Готов",
  DELIVERED: "Доставлен",
  CANCELLED: "Отменён",
};

export default function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`status ${status}`}>{LABELS[status]}</span>;
}
