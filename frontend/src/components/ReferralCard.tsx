import { useEffect, useState } from "react";
import { api, formatPrice } from "../api";
import { haptic, showAlert, tg } from "../telegram";
import type { ReferralInfo } from "../types";

export default function ReferralCard() {
  const [info, setInfo] = useState<ReferralInfo | null>(null);

  useEffect(() => {
    void api.getReferral().then(setInfo);
  }, []);

  if (!info) return null;

  const share = () => {
    haptic();
    const text = `Еда Рядом — домашняя еда рядом. Бонус ${info.referee_bonus} ₽ на первый заказ!`;
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(info.link)}&text=${encodeURIComponent(text)}`;
    if (tg?.openTelegramLink) {
      tg.openTelegramLink(shareUrl);
    } else if (navigator.share) {
      void navigator.share({ title: "Еда Рядом", text, url: info.link });
    } else {
      void navigator.clipboard.writeText(info.link);
      showAlert("Ссылка скопирована!");
    }
  };

  const copy = () => {
    haptic("success");
    void navigator.clipboard.writeText(info.link);
    showAlert("Ссылка скопирована");
  };

  return (
    <div className="card referral-card">
      <div className="referral-glow" />
      <strong className="referral-title">Пригласи друга</strong>
      <p className="hint referral-desc">
        Друг — <b>{formatPrice(info.referee_bonus)}</b> после первого заказа · вы —{" "}
        <b>{formatPrice(info.referrer_bonus)}</b>
      </p>
      <div className="referral-stats">
        <span>
          Баланс <strong>{formatPrice(info.balance)}</strong>
        </span>
        <span>
          Приглашено <strong>{info.invited_count}</strong>
        </span>
      </div>
      <p className="hint" style={{ margin: "8px 0 0", fontSize: 11 }}>
        До {info.max_discount_percent}% заказа списывается с баланса
      </p>
      <div className="btn-row" style={{ marginTop: 12 }}>
        <button type="button" className="btn small" onClick={share}>
          Поделиться
        </button>
        <button type="button" className="btn small secondary" onClick={copy}>
          Копировать
        </button>
      </div>
    </div>
  );
}
