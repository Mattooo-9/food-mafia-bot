/** Telegram кладёт init-data в hash — чиним URL до старта React Router. */
export function normalizeLaunchUrl(): void {
  const { hash, pathname, search } = window.location;

  if (hash.startsWith("#/")) {
    window.history.replaceState(null, "", hash.slice(1) + search);
    return;
  }

  if (hash && hash !== "#") {
    window.history.replaceState(null, "", pathname + search);
  }
}
