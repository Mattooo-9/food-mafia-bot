import FoodCard from "./FoodCard";
import CookCard from "./CookCard";
import type { AssistantGroup, Cook, Food } from "../types";

interface Props {
  groups: AssistantGroup[];
  onToggleFavoriteFood?: (food: Food) => void;
  onToggleFavoriteCook?: (cook: Cook) => void;
}

export default function AiResultGroups({ groups, onToggleFavoriteFood, onToggleFavoriteCook }: Props) {
  if (groups.length === 0) return null;

  return (
    <div className="ai-groups">
      {groups.map((group) => (
        <section key={`${group.kind}-${group.title}`} className="ai-group">
          <header className="ai-group-head">
            <h2>{group.title}</h2>
            {group.subtitle && <span>{group.subtitle}</span>}
          </header>
          {group.foods.map((food) => (
            <FoodCard key={food.id} food={food} onToggleFavorite={onToggleFavoriteFood} />
          ))}
          {group.cooks.map((cook) => (
            <CookCard key={cook.id} cook={cook} onToggleFavorite={onToggleFavoriteCook} />
          ))}
        </section>
      ))}
    </div>
  );
}
