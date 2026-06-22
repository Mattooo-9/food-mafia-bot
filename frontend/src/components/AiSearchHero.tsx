import { useEffect, useState } from "react";

interface Props {
  onChange: (value: string) => void;
  placeholder?: string;
  value: string;
}

export default function AiSearchHero({
  onChange,
  placeholder = "Например: недорогой борщ рядом…",
  value,
}: Props) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  useEffect(() => {
    const timer = window.setTimeout(() => onChange(local.trim()), 350);
    return () => window.clearTimeout(timer);
  }, [local, onChange]);

  return (
    <div className="ai-search-hero">
      <div className="ai-search-glow" />
      <div className="ai-search-inner">
        <span className="ai-search-spark">✨</span>
        <input
          type="search"
          enterKeyHint="search"
          placeholder={placeholder}
          value={local}
          onChange={(e) => setLocal(e.target.value)}
          autoComplete="off"
        />
        {local && (
          <button type="button" className="search-clear" onClick={() => setLocal("")} aria-label="Очистить">
            ✕
          </button>
        )}
      </div>
      <p className="ai-search-hint">ИИ сам поймёт категорию, расстояние и цену — вам только написать</p>
    </div>
  );
}
