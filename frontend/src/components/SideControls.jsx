import React from "react";
import "../styles/side-controls.css";
import { useTheme } from "../contexts/ThemeContext";
import { useLocale, SUPPORTED_LOCALES } from "../contexts/LocaleContext";
import { useFontSize } from "../contexts/FontSizeContext";

export default function SideControls() {
  const { theme, toggleTheme } = useTheme();
  const { locale, setLocale, t } = useLocale();
  const { increase, decrease, reset } = useFontSize();

  const switchLocale = () => {
    const idx = SUPPORTED_LOCALES.indexOf(locale);
    const next = SUPPORTED_LOCALES[(idx + 1) % SUPPORTED_LOCALES.length];
    setLocale(next);
  };

  return (
    <div className="side-controls" aria-hidden={false}>
      <div className="side-controls-inner" role="group" aria-label={t("sideControls.group")}>
        <button
          className="sc-btn sc-theme"
          onClick={toggleTheme}
          title={theme === "dark" ? t("sideControls.lightMode") : t("sideControls.darkMode")}
          aria-label={t("sideControls.toggleTheme")}
        >
          {theme === "dark" ? "☀️" : "🌙"}
          <span className="sc-label">{theme === "dark" ? t("sideControls.light") : t("sideControls.dark")}</span>
        </button>

        <button
          className="sc-btn sc-lang"
          onClick={switchLocale}
          title={t("sideControls.switchLang")}
          aria-label={t("sideControls.switchLang")}
        >
          🌐
          <span className="sc-label">{locale.toUpperCase()}</span>
        </button>

        <div className="sc-zoom">
          <button className="sc-btn sc-zoom-in" onClick={increase} title={t("sideControls.zoomIn")} aria-label={t("sideControls.zoomIn")}>
            ＋
          </button>
          <button className="sc-btn sc-zoom-out" onClick={decrease} title={t("sideControls.zoomOut")} aria-label={t("sideControls.zoomOut")}>
            －
          </button>
          <button className="sc-btn sc-zoom-reset" onClick={reset} title={t("sideControls.zoomReset")} aria-label={t("sideControls.zoomReset")}>
            ⤾
          </button>
          <span className="sc-label">{t("sideControls.zoom")}</span>
        </div>
      </div>
    </div>
  );
}
