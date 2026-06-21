import { ORDER_STATUS_LABELS } from "../constants";
import type { OrderStatus } from "../types";

export default function StatusBadge({ status }: { status: OrderStatus }) {
  return <span className={`status ${status}`}>{ORDER_STATUS_LABELS[status]}</span>;
}
