import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { api } from "./api";
import { applyBundle, setLocale } from "./i18n";
import type { AppConfig, User } from "./types";

interface UserContextValue {
  user: User | null;
  config: AppConfig | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  requestLocation: () => Promise<boolean>;
}

const UserContext = createContext<UserContextValue>({
  user: null,
  config: null,
  loading: true,
  error: null,
  refresh: async () => {},
  requestLocation: async () => false,
});

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const me = await api.getMe();
      const cfg = await api.getAppConfig();
      setLocale(me.locale);
      applyBundle(cfg.region.locale, cfg.strings);
      setUser(me);
      setConfig(cfg);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить профиль");
    } finally {
      setLoading(false);
    }
  }, []);

  const requestLocation = useCallback(async (): Promise<boolean> => {
    if (!navigator.geolocation) return false;
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          try {
            const updated = await api.setLocation(pos.coords.latitude, pos.coords.longitude);
            setUser(updated);
            if (!updated.onboarding_done) {
              const done = await api.completeOnboarding();
              setUser(done);
            }
            resolve(true);
          } catch {
            resolve(false);
          }
        },
        () => resolve(false),
        { enableHighAccuracy: false, timeout: 10000 },
      );
    });
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!loading && user && !user.has_location) {
      void requestLocation();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user?.id]);

  return (
    <UserContext.Provider value={{ user, config, loading, error, refresh, requestLocation }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser(): UserContextValue {
  return useContext(UserContext);
}
