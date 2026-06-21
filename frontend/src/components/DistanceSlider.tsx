import { formatDistance } from "../api";

const MIN = 500;
const MAX = 10000;
const STEP = 250;

interface Props {
  value: number;
  onChange: (meters: number) => void;
}

export default function DistanceSlider({ value, onChange }: Props) {
  return (
    <div className="distance-slider">
      <div className="distance-slider-head">
        <span>Рядом</span>
        <strong>{formatDistance(value)}</strong>
      </div>
      <input
        type="range"
        min={MIN}
        max={MAX}
        step={STEP}
        value={value}
        onInput={(e) => onChange(Number(e.currentTarget.value))}
        aria-label="Расстояние поиска"
      />
      <div className="distance-slider-labels">
        <span>{formatDistance(MIN)}</span>
        <span>{formatDistance(MAX)}</span>
      </div>
    </div>
  );
}
