import type { CategoryGroup } from "../types";

interface Props {
  groups: CategoryGroup[];
  selected: string | null;
  onSelect: (path: string | null) => void;
}

const SEP = " › ";

function path(group: string, category: string, subgroup?: string) {
  return subgroup ? `${group}${SEP}${category}${SEP}${subgroup}` : `${group}${SEP}${category}`;
}

export default function CategoryColumn({ groups, selected, onSelect }: Props) {
  return (
    <nav className="cat-column" aria-label="Категории">
      <button
        type="button"
        className={`cat-item ${selected === null ? "active" : ""}`}
        onClick={() => onSelect(null)}
      >
        Все
      </button>
      {groups.map((g) => (
        <div key={g.group} className="cat-group">
          <div className="cat-group-title">{g.group}</div>
          {g.categories.map((c) => (
            <div key={c.name} className="cat-category">
              <button
                type="button"
                className={`cat-item ${selected === path(g.group, c.name) ? "active" : ""}`}
                onClick={() => onSelect(path(g.group, c.name))}
              >
                {c.name}
              </button>
              {c.subgroups.map((sub) => {
                const full = path(g.group, c.name, sub);
                return (
                  <button
                    key={full}
                    type="button"
                    className={`cat-subitem ${selected === full ? "active" : ""}`}
                    onClick={() => onSelect(full)}
                  >
                    {sub}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      ))}
    </nav>
  );
}
