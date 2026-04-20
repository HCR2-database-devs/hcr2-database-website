import { useEffect, useState } from "react";

const storageKey = "darkMode";

export function useDarkMode() {
  const [isDark, setIsDark] = useState(() => localStorage.getItem(storageKey) === "true");

  useEffect(() => {
    if (isDark) {
      document.documentElement.setAttribute("data-theme", "dark");
      localStorage.setItem(storageKey, "true");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem(storageKey, "false");
    }
  }, [isDark]);

  return {
    isDark,
    toggleDarkMode: () => setIsDark((current) => !current)
  };
}
