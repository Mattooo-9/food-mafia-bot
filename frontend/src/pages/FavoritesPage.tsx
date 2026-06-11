import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import CookCard from "../components/CookCard";
import FoodCard from "../components/FoodCard";
import Spinner from "../components/Spinner";
import { haptic } from "../telegram";
import type { Cook, Food } from "../types";

export default function FavoritesPage() {
  const [tab, setTab] = useState<"foods" | "cooks">("foods");
  const [foods, setFoods] = useState<Food[]>([]);
  const [cooks, setCooks] = useState<Cook[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [foodsData, cooksData] = await Promise.all([
        api.getFavoriteFoods(),
        api.getFavoriteCooks(),
      ]);
      setFoods(foodsData);
      setCooks(cooksData);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const removeFood = async (food: Food) => {
    haptic();
    await api.removeFavoriteFood(food.id);
    setFoods((prev) => prev.filter((f) => f.id !== food.id));
  };

  const removeCook = async (cook: Cook) => {
    haptic();
    await api.removeFavoriteCook(cook.id);
    setCooks((prev) => prev.filter((c) => c.id !== cook.id));
  };

  if (loading) return <Spinner />;

  return (
    <div className="page">
      <h1 className="page-title">Избранное ❤️</h1>
      <div className="chips">
        <button className={`chip ${tab === "foods" ? "active" : ""}`} onClick={() => setTab("foods")}>
          🍲 Блюда ({foods.length})
        </button>
        <button className={`chip ${tab === "cooks" ? "active" : ""}`} onClick={() => setTab("cooks")}>
          👨‍🍳 Повара ({cooks.length})
        </button>
      </div>

      {tab === "foods" &&
        (foods.length === 0 ? (
          <div className="empty">
            <span className="emoji">🤍</span>Нет избранных блюд
          </div>
        ) : (
          foods.map((food) => <FoodCard key={food.id} food={food} onToggleFavorite={removeFood} />)
        ))}

      {tab === "cooks" &&
        (cooks.length === 0 ? (
          <div className="empty">
            <span className="emoji">🤍</span>Нет избранных поваров
          </div>
        ) : (
          cooks.map((cook) => <CookCard key={cook.id} cook={cook} onToggleFavorite={removeCook} />)
        ))}
    </div>
  );
}
