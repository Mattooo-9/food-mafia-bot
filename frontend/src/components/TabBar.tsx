import { NavLink } from "react-router-dom";
import { TABS } from "../constants";

interface Props {
  isCook: boolean;
}

const tabClass = ({ isActive }: { isActive: boolean }) => (isActive ? "active" : "");

export default function TabBar({ isCook }: Props) {
  const tabs = TABS.filter((t) => !t.cookOnly || isCook);

  return (
    <nav className="tabbar">
      {tabs.map((tab) => (
        <NavLink key={tab.to} to={tab.to} end={tab.end} className={tabClass}>
          <span className="tab-icon">{tab.icon}</span>
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
