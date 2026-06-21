import { useEffect, useRef } from "react";
import { TonConnectButton, useTonAddress, useTonConnectUI } from "@tonconnect/ui-react";
import { api, ApiError } from "../api";
import { haptic, showAlert } from "../telegram";

interface Props {
  savedAddress: string | null;
  onSaved: () => void;
}

export default function PaymentWallet({ savedAddress, onSaved }: Props) {
  const [tonConnectUI] = useTonConnectUI();
  const connectedAddress = useTonAddress();
  const syncing = useRef(false);

  useEffect(() => {
    if (!connectedAddress || syncing.current) return;
    if (connectedAddress === savedAddress) return;

    syncing.current = true;
    void (async () => {
      try {
        await api.setWallet(connectedAddress);
        haptic("success");
        onSaved();
      } catch (e) {
        haptic("error");
        showAlert(e instanceof ApiError ? e.message : "Не удалось сохранить кошелёк");
        await tonConnectUI.disconnect();
      } finally {
        syncing.current = false;
      }
    })();
  }, [connectedAddress, savedAddress, onSaved, tonConnectUI]);

  const disconnect = async () => {
    haptic();
    await tonConnectUI.disconnect();
    try {
      await api.setWallet(null);
      onSaved();
    } catch (e) {
      showAlert(e instanceof ApiError ? e.message : "Не удалось отключить кошелёк");
    }
  };

  return (
    <div className="card">
      <strong>💎 TON-кошелёк для оплаты</strong>
      <p className="hint" style={{ marginTop: 8 }}>
        Приватные ключи остаются в вашем кошельке. Мы сохраняем только публичный адрес для приёма
        TON от покупателей.
      </p>
      <div style={{ marginTop: 12 }}>
        <TonConnectButton />
      </div>
      {savedAddress && (
        <div style={{ marginTop: 12 }}>
          <p className="hint">
            Адрес: <code>{savedAddress.slice(0, 8)}…{savedAddress.slice(-6)}</code>
          </p>
          <button type="button" className="btn small secondary" onClick={() => void disconnect()}>
            Отключить
          </button>
        </div>
      )}
    </div>
  );
}
