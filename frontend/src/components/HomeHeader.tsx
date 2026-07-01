import LocationBar from "./LocationBar";
import { t } from "../i18n";

interface Props {
  hasLocation: boolean;
}

export default function HomeHeader({ hasLocation }: Props) {
  return (
    <header className="home-top panel">
      <h1 className="home-title">{t("app.title")}</h1>
      <LocationBar compact active={hasLocation} />
    </header>
  );
}
