import { useRef, type FormEvent } from "react";
import { hideKeyboard, haptic } from "../telegram";
import AppIcon from "./icons";

interface Props {
  draft: string;
  onDraftChange: (value: string) => void;
  onSearch: (value: string) => void;
  onClear?: () => void;
  suggestions?: string[];
  showChips?: boolean;
  placeholder?: string;
}

export default function AiSearchHero({
  draft,
  onDraftChange,
  onSearch,
  onClear,
  suggestions = [],
  showChips = true,
  placeholder = "Что хотите поесть?",
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const q = draft.trim();
    hideKeyboard();
    haptic();
    onSearch(q);
  };

  const pickChip = (label: string) => {
    onDraftChange(label);
    hideKeyboard();
    haptic();
    onSearch(label);
  };

  const chips = suggestions.slice(0, 4);

  return (
    <div className="ai-search-hero">
      <form className="ai-search-inner" onSubmit={submit}>
        <span className="ai-search-icon">
          <AppIcon name="search" size={20} />
        </span>
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
              onClear?.();
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
      </form>
      {showChips && chips.length > 0 && (
        <div className="ai-chips">
          {chips.map((chip) => (
            <button key={chip} type="button" className="ai-chip" onClick={() => pickChip(chip)}>
              {chip}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
