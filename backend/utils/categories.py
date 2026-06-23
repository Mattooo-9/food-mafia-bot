"""Дерево категорий: группа → категория → подгруппа (алфавитный порядок)."""

from __future__ import annotations

SEP = " › "

# group → category → [subgroups]
_RAW_TREE: dict[str, dict[str, list[str]]] = {
    "Выпечка и сладкое": {
        "Выпечка": ["Блины", "Пироги", "Хлеб"],
        "Десерты": ["Печенье", "Торты"],
    },
    "Горячие блюда": {
        "Основные": ["Гарниры", "Мясные", "Птица", "Рыба"],
        "Супы": ["Борщи", "Крем-супы", "Первые блюда"],
    },
    "Закуски и салаты": {
        "Закуски": [],
        "Салаты": [],
    },
    "На каждый день": {
        "Завтраки": [],
        "Напитки": ["Горячие", "Холодные"],
    },
    "Разное": {
        "Другое": [],
    },
}

# Старые плоские категории → новый путь
LEGACY_MAP: dict[str, str] = {
    "Выпечка": f"Выпечка и сладкое{SEP}Выпечка",
    "Горячее": f"Горячие блюда{SEP}Основные{SEP}Мясные",
    "Десерты": f"Выпечка и сладкое{SEP}Десерты",
    "Завтраки": f"На каждый день{SEP}Завтраки",
    "Закуски": f"Закуски и салаты{SEP}Закуски",
    "Напитки": f"На каждый день{SEP}Напитки",
    "Салаты": f"Закуски и салаты{SEP}Салаты",
    "Супы": f"Горячие блюда{SEP}Супы",
    "Другое": f"Разное{SEP}Другое",
}


def _sort_tree() -> dict[str, dict[str, list[str]]]:
    result: dict[str, dict[str, list[str]]] = {}
    for group in sorted(_RAW_TREE.keys(), key=lambda s: s.lower()):
        cats = _RAW_TREE[group]
        result[group] = {}
        for cat in sorted(cats.keys(), key=lambda s: s.lower()):
            subs = sorted(cats[cat], key=lambda s: s.lower())
            result[group][cat] = subs
    return result


CATEGORY_TREE = _sort_tree()


def path(group: str, category: str, subgroup: str | None = None) -> str:
    if subgroup:
        return f"{group}{SEP}{category}{SEP}{subgroup}"
    return f"{group}{SEP}{category}"


def all_paths() -> list[str]:
    out: list[str] = []
    for group, cats in CATEGORY_TREE.items():
        for cat, subs in cats.items():
            if subs:
                for sub in subs:
                    out.append(path(group, cat, sub))
            else:
                out.append(path(group, cat))
    return sorted(out, key=lambda s: s.lower())


def tree_for_api() -> list[dict]:
    groups: list[dict] = []
    for group, cats in CATEGORY_TREE.items():
        items: list[dict] = []
        for cat, subs in cats.items():
            items.append({"name": cat, "subgroups": subs})
        groups.append({"group": group, "categories": items})
    return groups


def normalize_category(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return path("Разное", "Другое")
    if v in LEGACY_MAP:
        return LEGACY_MAP[v]
    if SEP in v and v in set(all_paths()):
        return v
    if v in set(all_paths()):
        return v
    for p in all_paths():
        if p.endswith(SEP + v) or p == v:
            return p
    return v


def is_valid_category(value: str) -> bool:
    v = normalize_category(value)
    return v in set(all_paths()) or value in LEGACY_MAP


def leaf_name(category_path: str) -> str:
    return category_path.split(SEP)[-1] if SEP in category_path else category_path


# Ключевые слова → (group, category, subgroup|None)
_KEYWORD_RULES: list[tuple[list[str], str, str, str | None]] = [
    (["борщ", "щи", "уха", "солянк", "окрошк"], "Горячие блюда", "Супы", "Борщи"),
    (["крем-суп", "крем суп", "пюре-суп"], "Горячие блюда", "Супы", "Крем-супы"),
    (["суп", "бульон"], "Горячие блюда", "Супы", "Первые блюда"),
    (["стейк", "котлет", "гуляш", "шашлык", "фарш", "свинин", "говядин", "баран"], "Горячие блюда", "Основные", "Мясные"),
    (["куриц", "индейк", "утк", "курин", "окороч"], "Горячие блюда", "Основные", "Птица"),
    (["рыб", "лосос", "форел", "семг", "треск", "кревет", "мореп"], "Горячие блюда", "Основные", "Рыба"),
    (["рис", "греч", "картоф", "пюре", "макарон", "паста", "гарнир"], "Горячие блюда", "Основные", "Гарниры"),
    (["салат", "цезар", "оливье", "винегрет"], "Закуски и салаты", "Салаты", None),
    (["закуск", "бутерброд", "канапе", "ролл"], "Закуски и салаты", "Закуски", None),
    (["торт", "кекс", "мuffin", "маффин", "чизкейк"], "Выпечка и сладкое", "Десерты", "Торты"),
    (["печень", "печеньк", "cookie", "бисквит"], "Выпечка и сладкое", "Десерты", "Печенье"),
    (["десерт", "сладк", "шоколад", "морожен"], "Выпечка и сладкое", "Десерты", None),
    (["пирог", "пирож", "осетин", "хачапuri"], "Выпечка и сладкое", "Выпечка", "Пироги"),
    (["блин", "оладь", "сырник"], "Выпечка и сладкое", "Выпечка", "Блины"),
    (["хлеб", "булк", "лаваш"], "Выпечка и сладкое", "Выпечка", "Хлеб"),
    (["выпеч"], "Выпечка и сладкое", "Выпечка", None),
    (["завтрак", "каша", "омлет", "яичниц", "гранola"], "На каждый день", "Завтраки", None),
    (["кофе", "чай", "какао", "латte", "капуч"], "На каждый день", "Напитки", "Горячие"),
    (["сок", "лимонад", "смузи", "морс", "компот", "напит"], "На каждый день", "Напитки", "Холодные"),
]


def categorize_text(name: str = "", description: str = "", query: str = "") -> dict:
    text = f"{name} {description} {query}".lower().strip()
    best_score = 0
    best: tuple[str, str, str | None] = ("Разное", "Другое", None)

    for keywords, group, cat, sub in _KEYWORD_RULES:
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best = (group, cat, sub)

    group, cat, sub = best
    cat_path = path(group, cat, sub)
    parts = [group, cat] + ([sub] if sub else [])
    label = SEP.join(parts)
    return {
        "group": group,
        "category": cat,
        "subgroup": sub,
        "path": cat_path,
        "label": label,
        "score": best_score,
    }


def excluded_groups_for(cat: dict) -> list[str]:
    """Группы, которые не предлагать при явном запросе (суп ≠ выпечка)."""
    if cat.get("score", 0) < 1 or cat.get("group") in ("Разное", None):
        return []
    target = cat["group"]
    return [g for g in CATEGORY_TREE if g not in (target, "Разное")]


def food_group(category_path: str) -> str:
    fc = normalize_category(category_path)
    return fc.split(SEP)[0] if SEP in fc else fc


def food_matches_intent(food_category: str, cat_hint: dict, exclude_groups: list[str]) -> bool:
    group = food_group(food_category)
    if exclude_groups and group in exclude_groups:
        return False
    if cat_hint.get("score", 0) >= 1 and cat_hint.get("group") not in ("Разное", None):
        if group != cat_hint["group"]:
            return False
        return category_matches_filter(food_category, cat_hint["path"])
    return True


def category_matches_filter(food_category: str, filter_path: str | None) -> bool:
    if not filter_path:
        return True
    fc = normalize_category(food_category)
    fp = normalize_category(filter_path)
    return fc == fp or fc.startswith(fp + SEP) or fp in fc
