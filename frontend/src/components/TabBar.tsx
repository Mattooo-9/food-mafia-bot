import { NavLink } from "react-router-dom";
import { TAB_KEYS, t } from "../i18n";
import AppIcon from "./icons";

interface Props {
  isCook: boolean;
}

const tabClass = ({ isActive }: { isActive: boolean }) => (isActive ? "active" : "");

export default function TabBar({ isCook }: Props) {
  const tabs = TAB_KEYS.filter((tab) => !tab.cookOnly || isCook);

  return (
    <nav className="tabbar">
      {tabs.map((tab) => (
        <NavLink key={tab.to} to={tab.to} end={tab.end} className={tabClass}>
          <span className="tab-icon">
            <AppIcon name={tab.icon} size={22} />
          </span>
          {t(tab.labelKey)}
        </NavLink>
      ))}
    </nav>
  );
}
