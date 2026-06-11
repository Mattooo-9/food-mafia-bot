interface TelegramWebApp {
  initData: string;
  ready: () => void;
  expand: () => void;
  colorScheme: "light" | "dark";
  HapticFeedback?: {
    notificationOccurred: (type: "error" | "success" | "warning") => void;
    impactOccurred: (style: "light" | "medium" | "heavy") => void;
  };
  BackButton: {
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  };
  showAlert?: (message: string) => void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

export const tg: TelegramWebApp | undefined = window.Telegram?.WebApp;

export function initTelegram(): void {
  if (!tg) return;
  tg.ready();
  tg.expand();
  document.documentElement.dataset.theme = tg.colorScheme;
}

export function getInitData(): string {
  return tg?.initData ?? "";
}

export function haptic(type: "success" | "error" | "warning" = "success"): void {
  tg?.HapticFeedback?.notificationOccurred(type);
}

export function showAlert(message: string): void {
  if (tg?.showAlert) {
    tg.showAlert(message);
  } else {
    alert(message);
  }
}
