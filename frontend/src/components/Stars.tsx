interface Props {
  rating: number;
  count?: number;
}

export default function Stars({ rating, count }: Props) {
  if (!rating && !count) return <span className="hint">нет оценок</span>;
  const full = Math.round(rating);
  return (
    <span className="stars">
      {"★".repeat(full)}
      {"☆".repeat(5 - full)}
      <span className="hint"> {rating.toFixed(1)}{count != null ? ` (${count})` : ""}</span>
    </span>
  );
}
