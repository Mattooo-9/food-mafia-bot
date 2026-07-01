"""Переводы UI — fallback: запрошенный → en → ru."""

from __future__ import annotations

# Языки Telegram с полным или частичным покрытием (остальное → en).
_LOCALES = (
    "ru", "en", "uk", "uz", "kk", "de", "es", "fr", "it", "pt", "pl",
    "tr", "ar", "fa", "he", "id", "vi", "th", "zh", "ja", "ko", "be",
)

_STRINGS: dict[str, dict[str, str]] = {
    "tab.feed": {
        "ru": "Лента", "en": "Feed", "uk": "Стрічка", "uz": "Lenta", "kk": "Таспа",
        "de": "Feed", "es": "Inicio", "fr": "Fil", "tr": "Akış", "ar": "الخلاصة",
        "zh": "动态", "ja": "フィード", "ko": "피드", "pt": "Feed", "id": "Beranda",
    },
    "tab.cooks": {
        "ru": "Повара", "en": "Cooks", "uk": "Кухарі", "uz": "Oshpazlar", "kk": "Аспаздар",
        "de": "Köche", "es": "Cocineros", "fr": "Cuisiniers", "tr": "Aşçılar", "ar": "الطهاة",
        "zh": "厨师", "ja": "シェフ", "ko": "요리사", "pt": "Cozinheiros", "id": "Koki",
    },
    "tab.orders": {
        "ru": "Заказы", "en": "Orders", "uk": "Замовлення", "uz": "Buyurtmalar", "kk": "Тапсырыстар",
        "de": "Bestellungen", "es": "Pedidos", "fr": "Commandes", "tr": "Siparişler", "ar": "الطلبات",
        "zh": "订单", "ja": "注文", "ko": "주문", "pt": "Pedidos", "id": "Pesanan",
    },
    "tab.favorites": {
        "ru": "Избранное", "en": "Saved", "uk": "Обране", "uz": "Tanlangan", "kk": "Таңдаулы",
        "de": "Favoriten", "es": "Guardados", "fr": "Favoris", "tr": "Kayıtlı", "ar": "المفضلة",
        "zh": "收藏", "ja": "保存", "ko": "저장", "pt": "Salvos", "id": "Favorit",
    },
    "tab.kitchen": {
        "ru": "Кухня", "en": "Kitchen", "uk": "Кухня", "uz": "Oshxona", "kk": "Ас үй",
        "de": "Küche", "es": "Cocina", "fr": "Cuisine", "tr": "Mutfak", "ar": "المطبخ",
        "zh": "厨房", "ja": "キッチン", "ko": "주방", "pt": "Cozinha", "id": "Dapur",
    },
    "tab.profile": {
        "ru": "Профиль", "en": "Profile", "uk": "Профіль", "uz": "Profil", "kk": "Профиль",
        "de": "Profil", "es": "Perfil", "fr": "Profil", "tr": "Profil", "ar": "الملف", "zh": "资料",
    },
    "search.placeholder": {
        "ru": "Что хотите поесть?", "en": "What would you like?", "uk": "Що хочете з'їсти?",
        "uz": "Nima yeyishni xohlaysiz?", "kk": "Не ішкіңіз келеді?", "de": "Was möchten Sie essen?",
        "es": "¿Qué le gustaría comer?", "fr": "Que voulez-vous manger?", "tr": "Ne yemek istersiniz?",
        "ar": "ماذا تريد أن تأكل؟", "zh": "想吃什么？", "ja": "何を食べますか？", "ko": "무엇을 드시겠어요?",
    },
    "geo.enable": {
        "ru": "Гео", "en": "Geo", "uk": "Гео", "uz": "Geo", "kk": "Гео", "de": "Ort", "es": "Geo",
        "fr": "Geo", "tr": "Konum", "ar": "الموقع", "zh": "定位", "ja": "位置", "ko": "위치",
    },
    "geo.nearby": {
        "ru": "Рядом", "en": "Nearby", "uk": "Поруч", "uz": "Yaqinda", "kk": "Жақын",
        "de": "In der Nähe", "es": "Cerca", "fr": "À proximité", "tr": "Yakında", "ar": "بالقرب",
        "zh": "附近", "ja": "近く", "ko": "근처",
    },
    "companion.no_geo": {
        "ru": "Включите «Гео» в шапке — покажем блюда рядом.",
        "en": "Turn on Geo in the header to see food nearby.",
        "uk": "Увімкніть «Гео» — покажемо страви поруч.",
        "uz": "Yaqin atrofdagi taomlar uchun «Geo»ni yoqing.",
        "kk": "Жақын маңдағы тағамдар үшін «Geo» қосыңыз.",
        "de": "Aktivieren Sie Geo, um Gerichte in der Nähe zu sehen.",
        "es": "Active Geo para ver comida cercana.",
        "fr": "Activez Geo pour voir les plats à proximité.",
        "tr": "Yakındaki yemekler için Geo'yu açın.",
        "ar": "فعّل الموقع لرؤية الطعام القريب.",
        "zh": "开启定位以查看附近美食。",
    },
    "companion.search_empty": {
        "ru": "Нет в ленте — опишите запрос во вкладке «Заказы».",
        "en": "Not in feed — describe your request in Orders.",
        "uk": "Немає в стрічці — опишіть у «Замовлення».",
        "uz": "Lentada yo'q — «Buyurtmalar»da yozing.",
        "kk": "Таспада жоқ — «Тапсырыстар»да сипаттаңыз.",
        "de": "Nicht im Feed — Anfrage unter Bestellungen.",
        "es": "No está en el feed — descríbalo en Pedidos.",
        "fr": "Absent du fil — décrivez dans Commandes.",
        "tr": "Akışta yok — Siparişler'de yazın.",
        "ar": "غير متوفر — صِف الطلب في الطلبات.",
        "zh": "未找到 — 请在订单中描述需求。",
    },
    "companion.no_supply": {
        "ru": "Рядом пока пусто — загляните позже или оставьте запрос в «Заказах».",
        "en": "Nothing nearby yet — check later or request in Orders.",
        "uk": "Поруч поки порожньо — зайдіть пізніше або в «Замовлення».",
        "uz": "Hozircha bo'sh — keyinroq yoki «Buyurtmalar»da.",
        "kk": "Әзірге бос — кейінірек немесе «Тапсырыстар»да.",
        "de": "Noch nichts in der Nähe — später oder unter Bestellungen.",
        "es": "Nada cerca aún — más tarde o en Pedidos.",
        "fr": "Rien à proximité — plus tard ou dans Commandes.",
        "tr": "Yakında henüz yok — sonra veya Siparişler'de.",
        "ar": "لا شيء قريبًا — لاحقًا أو في الطلبات.",
        "zh": "附近暂无 — 稍后再看或在订单中请求。",
    },
    "meal.morning": {"ru": "Завтрак", "en": "Breakfast", "uk": "Сніданок", "de": "Frühstück", "es": "Desayuno", "tr": "Kahvaltı", "ar": "فطور", "zh": "早餐"},
    "meal.lunch": {"ru": "Обед", "en": "Lunch", "uk": "Обід", "de": "Mittagessen", "es": "Almuerzo", "tr": "Öğle", "ar": "غداء", "zh": "午餐"},
    "meal.afternoon": {"ru": "Перекус", "en": "Snack", "uk": "Перекус", "de": "Snack", "es": "Merienda", "tr": "Atıştırma", "zh": "加餐"},
    "meal.evening": {"ru": "Ужин", "en": "Dinner", "uk": "Вечеря", "de": "Abendessen", "es": "Cena", "tr": "Akşam", "ar": "عشاء", "zh": "晚餐"},
    "meal.night": {"ru": "Ночь", "en": "Late night", "uk": "Ніч", "de": "Spät", "es": "Noche", "tr": "Gece", "zh": "夜宵"},
    "hint.kcal_left": {
        "ru": "На {meal} осталось ~{kcal} ккал",
        "en": "~{kcal} kcal left for {meal}",
        "uk": "На {meal} залишилось ~{kcal} ккал",
        "de": "~{kcal} kcal für {meal}",
        "es": "~{kcal} kcal para {meal}",
        "tr": "{meal} için ~{kcal} kcal",
        "zh": "{meal} 还剩约 {kcal} 千卡",
    },
    "hint.rainbow": {
        "ru": "Добавьте разноцветные овощи",
        "en": "Add colorful vegetables",
        "uk": "Додайте різні овочі",
        "de": "Mehr Gemüse",
        "es": "Más verduras",
        "tr": "Sebze ekleyin",
        "zh": "多吃些蔬菜",
    },
    "group.pick": {"ru": "Выбор", "en": "Pick", "uk": "Вибір", "de": "Auswahl", "es": "Elección", "tr": "Seçim", "zh": "推荐"},
    "group.d800": {"ru": "До 800 м", "en": "Within 800 m", "uk": "До 800 м", "de": "Bis 800 m", "es": "Hasta 800 m", "tr": "800 m içi", "zh": "800米内"},
    "group.d2k": {"ru": "До 2 км", "en": "Within 2 km", "uk": "До 2 км", "de": "Bis 2 km", "es": "Hasta 2 km", "tr": "2 km içi", "zh": "2公里内"},
    "group.d5k": {"ru": "До 5 км", "en": "Within 5 km", "uk": "До 5 км", "de": "Bis 5 km", "es": "Hasta 5 km", "tr": "5 km içi", "zh": "5公里内"},
    "group.further": {"ru": "Дальше", "en": "Farther", "uk": "Далі", "de": "Weiter", "es": "Más lejos", "tr": "Uzak", "zh": "更远"},
    "group.no_distance": {"ru": "Без расстояния", "en": "No distance", "uk": "Без відстані", "de": "Ohne Entfernung", "zh": "无距离"},
    "group.c1k": {"ru": "До 1 км", "en": "Within 1 km", "uk": "До 1 км", "de": "Bis 1 km", "zh": "1公里内"},
    "group.c3k": {"ru": "До 3 км", "en": "Within 3 km", "uk": "До 3 км", "de": "Bis 3 km", "zh": "3公里内"},
    "group.cooks": {"ru": "Повара", "en": "Cooks", "uk": "Кухарі", "de": "Köche", "es": "Cocineros", "zh": "厨师"},
    "geo.nearby_section": {"ru": "Рядом", "en": "Nearby", "uk": "Поруч", "de": "In der Nähe", "es": "Cerca", "tr": "Yakında", "zh": "附近"},
    "search.not_found": {"ru": "Не найдено", "en": "Not found", "uk": "Не знайдено", "de": "Nicht gefunden", "es": "No encontrado", "zh": "未找到"},
    "error.auth": {
        "ru": "Откройте приложение через Telegram",
        "en": "Open the app from Telegram",
        "uk": "Відкрийте через Telegram",
        "de": "Öffnen Sie die App über Telegram",
        "es": "Abra la app desde Telegram",
        "tr": "Uygulamayı Telegram'dan açın",
        "ar": "افتح التطبيق من تيليجرام",
        "zh": "请通过 Telegram 打开应用",
    },
    "app.title": {"ru": "Еда Рядом", "en": "Food Nearby", "uk": "Їжа Поруч", "uz": "Yaqin Ovqat", "kk": "Жақын Тамақ", "de": "Essen in der Nähe", "es": "Comida Cerca", "tr": "Yakın Yemek", "ar": "طعام قريب", "zh": "附近美食"},
}


def normalize_locale(code: str | None, preferred: str | None = None) -> str:
    if preferred:
        base = preferred.split("-")[0].lower()
        if base in _LOCALES:
            return base
    if code:
        base = code.split("-")[0].lower()
        if base in _LOCALES:
            return base
    return "en"


def t(locale: str | None, key: str, **kwargs: str) -> str:
    loc = normalize_locale(None, locale)
    bucket = _STRINGS.get(key, {})
    text = bucket.get(loc) or bucket.get("en") or bucket.get("ru") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def bundle_for(locale: str | None) -> dict[str, str]:
    loc = normalize_locale(None, locale)
    out: dict[str, str] = {}
    for key, translations in _STRINGS.items():
        out[key] = translations.get(loc) or translations.get("en") or translations.get("ru") or key
    return out


def supported_locales() -> list[str]:
    return list(_LOCALES)
