import LocationBar from "./LocationBar";

interface Props {
  hasLocation: boolean;
}

export default function HomeHeader({ hasLocation }: Props) {
  return (
    <header className="home-top panel">
      <h1 className="home-title">Еда Рядом</h1>
      <LocationBar compact active={hasLocation} />
    </header>
  );
}
