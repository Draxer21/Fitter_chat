import React from "react";
import "../styles/side-controls.css";
import { useTheme } from "../contexts/ThemeContext";
import { useLocale, SUPPORTED_LOCALES } from "../contexts/LocaleContext";
import { useFontSize } from "../contexts/FontSizeContext";

export default function SideControls() {
  const { theme, toggleTheme } = useTheme();
  const { locale, setLocale } = useLocale();
  const { increase, decrease, reset } = useFontSize();

  const switchLocale = () => {
    const idx = SUPPORTED_LOCALES.indexOf(locale);
    const next = SUPPORTED_LOCALES[(idx + 1) % SUPPORTED_LOCALES.length];
    setLocale(next);
  };

  return (
    <div className="side-controls" aria-hidden={false}>
      <div className="side-controls-inner" role="group" aria-label="Controles laterales">
        <button
          className="sc-btn sc-theme"
          onClick={toggleTheme}
          title={theme === "dark" ? "Modo claro" : "Modo oscuro"}
          aria-label="Alternar modo"
        >
          {theme === "dark" ? "☀️" : "🌙"}
          <span className="sc-label">{theme === "dark" ? "Claro" : "Oscuro"}</span>
        </button>

        <button
          className="sc-btn sc-lang"
          onClick={switchLocale}
          title="Cambiar idioma"
          aria-label="Cambiar idioma"
        >
          🌐
          <span className="sc-label">{locale.toUpperCase()}</span>
        </button>

        <div className="sc-zoom">
          <button className="sc-btn sc-zoom-in" onClick={increase} title="Acercar" aria-label="Acercar">
            ＋
          </button>
          <button className="sc-btn sc-zoom-out" onClick={decrease} title="Alejar" aria-label="Alejar">
            －
          </button>
          <button className="sc-btn sc-zoom-reset" onClick={reset} title="Resetear zoom" aria-label="Resetear zoom">
            ⤾
          </button>
          <span className="sc-label">Zoom</span>
        </div>
      </div>
    </div>
  );
}
