import type { ReactNode } from "react";
import { Route, Routes, Navigate } from "react-router-dom";
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
import { t } from "./i18n";

function CookOnly({ children }: { children: ReactNode }) {
  const { user } = useUser();
  if (!user?.is_cook) return <Navigate to="/profile" replace />;
  return <>{children}</>;
}

function AppInner() {
  const { user, loading, error } = useUser();

  if (loading) {
    return (
      <div className="app-loading">
        <Spinner />
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="error-screen">
        <h1>{t("app.title")}</h1>
        <p>{error ?? t("app.error")}</p>
        <p className="hint">{t("app.hint")}</p>
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
        <Route path="/my-kitchen" element={<CookOnly><MyKitchenPage /></CookOnly>} />
        <Route path="/my-kitchen/dish/new" element={<CookOnly><DishFormPage /></CookOnly>} />
        <Route path="/my-kitchen/dish/:id" element={<CookOnly><DishFormPage /></CookOnly>} />
        <Route path="*" element={<Navigate to="/" replace />} />
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
