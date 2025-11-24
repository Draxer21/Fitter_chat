import { createContext, useContext, useEffect, useMemo, useState } from "react";

const FontSizeContext = createContext({
  scale: 1,
  increase: () => {},
  decrease: () => {},
  reset: () => {},
});

const STORAGE_KEY = "font-size-scale";
const MIN_SCALE = 0.9;
const MAX_SCALE = 1.2;
const STEP = 0.1;

const clamp = (value) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, value));

export function FontSizeProvider({ children }) {
  const [scale, setScale] = useState(() => {
    const stored = parseFloat(localStorage.getItem(STORAGE_KEY));
    if (!Number.isNaN(stored) && stored >= MIN_SCALE && stored <= MAX_SCALE) {
      return stored;
    }
    return 1;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, String(scale));
    document.documentElement.style.setProperty("--font-scale", scale);
  }, [scale]);

  const value = useMemo(
    () => ({
      scale,
      increase: () => setScale((prev) => clamp(prev + STEP)),
      decrease: () => setScale((prev) => clamp(prev - STEP)),
      reset: () => setScale(1),
    }),
    [scale]
  );

  return <FontSizeContext.Provider value={value}>{children}</FontSizeContext.Provider>;
}

export const useFontSize = () => useContext(FontSizeContext);
