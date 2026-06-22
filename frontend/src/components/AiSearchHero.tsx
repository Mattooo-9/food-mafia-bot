import { useRef, type FormEvent } from "react";
import { hideKeyboard, haptic } from "../telegram";

interface Props {
  draft: string;
  onDraftChange: (value: string) => void;
  onSearch: (value: string) => void;
  placeholder?: string;
}

export default function AiSearchHero({
  draft,
  onDraftChange,
  onSearch,
  placeholder = "Например: недорогой борщ рядом…",
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const q = draft.trim();
    hideKeyboard();
    haptic();
    onSearch(q);
  };

  return (
    <form className="ai-search-hero" onSubmit={submit}>
      <div className="ai-search-glow" />
      <div className="ai-search-inner">
        <span className="ai-search-spark">✨</span>
        <input
          ref={inputRef}
          type="search"
          enterKeyHint="search"
          placeholder={placeholder}
          value={draft}
          onChange={(e) => onDraftChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
          autoComplete="off"
        />
        {draft ? (
          <button
            type="button"
            className="search-clear"
            onClick={() => {
              onDraftChange("");
            }}
            aria-label="Очистить"
          >
            ✕
          </button>
        ) : (
          <button type="submit" className="ai-search-go" aria-label="Найти">
            Найти
          </button>
        )}
      </div>
      <p className="ai-search-hint">Напишите и нажмите «Найти» — ИИ сам разложит по группам в базе</p>
    </form>
  );
}
