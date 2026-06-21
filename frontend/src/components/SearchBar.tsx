import { useEffect, useState } from "react";

interface Props {
  onChange: (value: string) => void;
  placeholder?: string;
  value: string;
}

export default function SearchBar({ onChange, placeholder = "Поиск...", value }: Props) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  useEffect(() => {
    const timer = window.setTimeout(() => onChange(local.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [local, onChange]);

  return (
    <div className="search-bar">
      <span className="search-icon">🔍</span>
      <input
        type="search"
        enterKeyHint="search"
        placeholder={placeholder}
        value={local}
        onChange={(e) => setLocal(e.target.value)}
      />
      {local && (
        <button type="button" className="search-clear" onClick={() => setLocal("")} aria-label="Очистить">
          ✕
        </button>
      )}
    </div>
  );
}
