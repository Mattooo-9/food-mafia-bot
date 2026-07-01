import { haptic, showAlert } from "../telegram";
import { useUser } from "../UserContext";
import { t } from "../i18n";
import AppIcon from "./icons";

interface Props {
  compact?: boolean;
  active?: boolean;
}

export default function LocationBar({ compact = false, active }: Props) {
  const { user, requestLocation } = useUser();
  const hasLocation = active ?? Boolean(user?.has_location);

  const update = async () => {
    const ok = await requestLocation();
    haptic(ok ? "success" : "error");
    if (!ok) {
      showAlert(t("geo.enable"));
    }
  };

  if (compact) {
    return (
      <button
        type="button"
        className={`geo-pill ${hasLocation ? "on" : ""}`}
        onClick={() => void update()}
        aria-label={hasLocation ? t("geo.nearby") : t("geo.enable")}
      >
        <AppIcon name={hasLocation ? "geoOn" : "geo"} size={16} />
        <span>{hasLocation ? t("geo.nearby") : t("geo.enable")}</span>
      </button>
    );
  }

  return (
    <div className={`location-bar panel ${hasLocation ? "active" : ""}`}>
      <AppIcon name={hasLocation ? "geoOn" : "geo"} size={18} />
      <span className="location-text">{hasLocation ? t("geo.nearby") : t("geo.enable")}</span>
      <button type="button" className="location-btn" onClick={() => void update()}>
        {hasLocation ? t("geo.nearby") : t("geo.enable")}
      </button>
    </div>
  );
}
