import { api } from "../api";
import { t } from "../i18n";
import { haptic } from "../telegram";
import { useUser } from "../UserContext";

export default function OnboardingStrip() {
  const { user, refresh, requestLocation } = useUser();
  if (!user || user.onboarding_done) return null;

  const finish = async () => {
    haptic("success");
    await api.completeOnboarding();
    await refresh();
  };

  const enableGeo = async () => {
    haptic();
    await requestLocation();
  };

  return (
    <section className="home-section">
      <div className="panel onboarding-strip">
        <strong>{t("onboarding.title")}</strong>
        <ol className="onboarding-steps">
          <li>{t("onboarding.step1")}</li>
          <li>{t("onboarding.step2")}</li>
          <li>{t("onboarding.step3")}</li>
        </ol>
        <div className="btn-row">
          {user.lat == null && (
            <button type="button" className="btn small" onClick={() => void enableGeo()}>
              {t("onboarding.geo")}
            </button>
          )}
          <button type="button" className="btn small secondary" onClick={() => void finish()}>
            {t("onboarding.done")}
          </button>
        </div>
      </div>
    </section>
  );
}
