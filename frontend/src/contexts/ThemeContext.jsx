import { createContext, useContext, useEffect, useMemo, useState } from "react";

const ThemeContext = createContext({ theme: "light", toggleTheme: () => {} });

const STORAGE_KEY = "theme-preference";

const getPreferredTheme = () => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return "light";
};

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => getPreferredTheme());

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, theme);
    const root = document.documentElement;
    const body = document.body;
    root.classList.toggle("theme-dark", theme === "dark");
    body.classList.toggle("theme-dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    const media = window.matchMedia?.("(prefers-color-scheme: dark)");
    const listener = (event) => {
      if (!localStorage.getItem(STORAGE_KEY)) {
        setTheme(event.matches ? "dark" : "light");
      }
    };
    media?.addEventListener?.("change", listener);
    return () => media?.removeEventListener?.("change", listener);
  }, []);

  const value = useMemo(
    () => ({
      theme,
      toggleTheme: () => setTheme((prev) => (prev === "dark" ? "light" : "dark")),
      setTheme,
    }),
    [theme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
