export type IconName =
  | "feed"
  | "cooks"
  | "orders"
  | "favorites"
  | "kitchen"
  | "profile"
  | "geo"
  | "geoOn"
  | "search"
  | "chef"
  | "clipboard"
  | "heart"
  | "heartOutline"
  | "distance"
  | "time"
  | "star";

interface Props {
  name: IconName;
  size?: number;
  className?: string;
}

export default function AppIcon({ name, size = 22, className }: Props) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
    className,
    "aria-hidden": true as const,
  };

  switch (name) {
    case "feed":
      return (
        <svg {...common}>
          <path
            d="M4 7.5h16M4 12h10M4 16.5h14"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
          <rect
            x="3"
            y="4"
            width="18"
            height="16"
            rx="3"
            stroke="currentColor"
            strokeWidth="1.6"
          />
          <circle cx="17.5" cy="12" r="2.2" fill="currentColor" opacity="0.85" />
        </svg>
      );
    case "cooks":
    case "chef":
      return (
        <svg {...common}>
          <path
            d="M6 11c0-2.8 2.2-5 5-5 .9 0 1.7.2 2.4.6C14.5 5.2 16 4 18 4c2.2 0 4 1.8 4 4 0 1.4-.7 2.6-1.8 3.3V20H4v-8.7C2.9 10.6 2 9.4 2 8c0-2.2 1.8-4 4-4 1.4 0 2.6.7 3.3 1.8"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
          <path d="M8 20v-3M12 20v-3M16 20v-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
    case "orders":
    case "clipboard":
      return (
        <svg {...common}>
          <rect x="5" y="4" width="14" height="18" rx="2.5" stroke="currentColor" strokeWidth="1.6" />
          <path
            d="M9 4.5h6a1.5 1.5 0 0 1 1.5 1.5V7H7.5V6A1.5 1.5 0 0 1 9 4.5Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <path d="M8.5 11h7M8.5 14.5h7M8.5 18h4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
    case "favorites":
    case "heart":
      return (
        <svg {...common}>
          <path
            d="M12 20.5s-6.8-4.4-8.6-8.4C1.9 8.8 3.6 5.5 6.8 5.2c1.8-.2 3.4.7 4.4 2 1-1.3 2.6-2.2 4.4-2 3.2.3 4.9 3.6 3.4 7-1.8 4-8.6 8.4-8.6 8.4Z"
            fill="currentColor"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "heartOutline":
      return (
        <svg {...common}>
          <path
            d="M12 20.5s-6.8-4.4-8.6-8.4C1.9 8.8 3.6 5.5 6.8 5.2c1.8-.2 3.4.7 4.4 2 1-1.3 2.6-2.2 4.4-2 3.2.3 4.9 3.6 3.4 7-1.8 4-8.6 8.4-8.6 8.4Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "kitchen":
      return (
        <svg {...common}>
          <path
            d="M4 10h16v10H4V10Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <path
            d="M7 10V7a5 5 0 0 1 10 0v3"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
          <path d="M9 14h6M9 17.5h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );
    case "profile":
      return (
        <svg {...common}>
          <circle cx="12" cy="8.5" r="3.5" stroke="currentColor" strokeWidth="1.6" />
          <path
            d="M5.5 20c.8-3.4 3.4-5.5 6.5-5.5s5.7 2.1 6.5 5.5"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </svg>
      );
    case "geo":
      return (
        <svg {...common}>
          <path
            d="M12 21s6-5.2 6-10a6 6 0 1 0-12 0c0 4.8 6 10 6 10Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <circle cx="12" cy="11" r="2.2" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      );
    case "geoOn":
      return (
        <svg {...common}>
          <path
            d="M12 21s6-5.2 6-10a6 6 0 1 0-12 0c0 4.8 6 10 6 10Z"
            fill="currentColor"
            fillOpacity="0.2"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <circle cx="12" cy="11" r="2.5" fill="currentColor" />
        </svg>
      );
    case "search":
      return (
        <svg {...common}>
          <circle cx="11" cy="11" r="5.5" stroke="currentColor" strokeWidth="1.7" />
          <path d="M15.5 15.5 20 20" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
    case "distance":
      return (
        <svg {...common}>
          <path
            d="M12 21s5-4.5 5-9a5 5 0 1 0-10 0c0 4.5 5 9 5 9Z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
          <circle cx="12" cy="12" r="1.8" fill="currentColor" />
        </svg>
      );
    case "time":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="1.6" />
          <path d="M12 7.5V12l3 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "star":
      return (
        <svg {...common}>
          <path
            d="m12 3.8 2.1 4.3 4.7.7-3.4 3.3.8 4.7L12 14.8 7.8 16.8l.8-4.7-3.4-3.3 4.7-.7L12 3.8Z"
            fill="currentColor"
            stroke="currentColor"
            strokeWidth="1"
            strokeLinejoin="round"
          />
        </svg>
      );
    default:
      return null;
  }
}
