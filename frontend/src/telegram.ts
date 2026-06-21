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
  onEvent?: (event: string, cb: () => void) => void;
  offEvent?: (event: string, cb: () => void) => void;
  openTelegramLink?: (url: string) => void;
  showAlert?: (message: string) => void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

export const tg: TelegramWebApp | undefined = window.Telegram?.WebApp;

function applyTheme(): void {
  if (!tg) return;
  document.documentElement.dataset.theme = tg.colorScheme;
}

export function initTelegram(): void {
  if (!tg) return;
  tg.ready();
  tg.expand();
  applyTheme();
  tg.onEvent?.("themeChanged", applyTheme);
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
