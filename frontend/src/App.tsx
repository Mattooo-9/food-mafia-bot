import { Route, Routes } from "react-router-dom";
import Spinner from "./components/Spinner";
import TabBar from "./components/TabBar";
import CookPage from "./pages/CookPage";
import CooksPage from "./pages/CooksPage";
import DishFormPage from "./pages/DishFormPage";
import FavoritesPage from "./pages/FavoritesPage";
import FeedPage from "./pages/FeedPage";
import FoodPage from "./pages/FoodPage";
import MyKitchenPage from "./pages/MyKitchenPage";
import OrdersPage from "./pages/OrdersPage";
import ProfilePage from "./pages/ProfilePage";
import { UserProvider, useUser } from "./UserContext";

function AppInner() {
  const { user, loading, error } = useUser();

  if (loading) return <Spinner />;

  if (error || !user) {
    return (
      <div className="empty">
        <span className="emoji">🔒</span>
        {error ?? "Откройте приложение через Telegram"}
        <p className="hint">Запустите бота и нажмите кнопку «Открыть Еда Рядом».</p>
      </div>
    );
  }

  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<FeedPage />} />
        <Route path="/food/:id" element={<FoodPage />} />
        <Route path="/cooks" element={<CooksPage />} />
        <Route path="/cook/:id" element={<CookPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/favorites" element={<FavoritesPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/my-kitchen" element={<MyKitchenPage />} />
        <Route path="/my-kitchen/dish/new" element={<DishFormPage />} />
        <Route path="/my-kitchen/dish/:id" element={<DishFormPage />} />
      </Routes>
      <TabBar isCook={user.is_cook} />
    </div>
  );
}

export default function App() {
  return (
    <UserProvider>
      <AppInner />
    </UserProvider>
  );
}
