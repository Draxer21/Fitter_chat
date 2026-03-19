import { useMemo } from "react";
import { useLocale } from "../contexts/LocaleContext";
import "../styles/plan-comparison.css";

export default function PlanComparisonModal({ planA, planB, planType, onClose }) {
  const { t } = useLocale();

  const isRoutine = planType === "routine";

  const comparison = useMemo(() => {
    if (!planA || !planB) return null;

    if (isRoutine) {
      const exA = planA.content?.exercises || [];
      const exB = planB.content?.exercises || [];
      const maxLen = Math.max(exA.length, exB.length);
      const rows = [];
      for (let i = 0; i < maxLen; i++) {
        const a = exA[i];
        const b = exB[i];
        const nameA = a?.nombre || a?.name || "";
        const nameB = b?.nombre || b?.name || "";
        const diff = nameA !== nameB || (a?.series !== b?.series) || (a?.repeticiones !== b?.repeticiones);
        rows.push({ a, b, diff });
      }
      return { rows, summaryA: planA.content?.summary || {}, summaryB: planB.content?.summary || {} };
    }

    // Diet comparison
    const mealsA = planA.content?.meals || [];
    const mealsB = planB.content?.meals || [];
    const maxLen = Math.max(mealsA.length, mealsB.length);
    const rows = [];
    for (let i = 0; i < maxLen; i++) {
      const a = mealsA[i];
      const b = mealsB[i];
      const diff = (a?.name !== b?.name) || (a?.items?.length !== b?.items?.length);
      rows.push({ a, b, diff });
    }
    return { rows, summaryA: planA.content?.summary || {}, summaryB: planB.content?.summary || {} };
  }, [planA, planB, isRoutine]);

  if (!comparison) return null;

  const fmtExercise = (ex) => {
    if (!ex) return "—";
    const name = ex.nombre || ex.name || "?";
    const s = ex.series ? `${ex.series}s` : "";
    const r = ex.repeticiones ? `${ex.repeticiones}r` : "";
    return [name, s, r].filter(Boolean).join(" · ");
  };

  const fmtMeal = (meal) => {
    if (!meal) return "—";
    const items = meal.items || [];
    const preview = items.slice(0, 3).map((it) => (typeof it === "string" ? it : it?.name || "?")).join(", ");
    return `${meal.name || "?"}: ${preview}${items.length > 3 ? "..." : ""}`;
  };

  return (
    <div className="plan-comparison-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label={t("comparison.title")}>
      <div className="plan-comparison-modal" onClick={(e) => e.stopPropagation()}>
        <div className="plan-comparison-header">
          <h2>{t("comparison.title")}</h2>
          <button className="btn btn-outline-secondary btn-sm" onClick={onClose}>{t("comparison.close")}</button>
        </div>

        <div className="plan-comparison-labels">
          <span className="plan-comparison-label">{planA.title || `${t(isRoutine ? "comparison.routine" : "comparison.diet")} A`}</span>
          <span className="plan-comparison-label">{planB.title || `${t(isRoutine ? "comparison.routine" : "comparison.diet")} B`}</span>
        </div>

        {/* Summary row */}
        {isRoutine ? (
          <div className="plan-comparison-summary">
            <div>{comparison.summaryA.objetivo || "—"} · {comparison.summaryA.nivel || "—"} · {comparison.summaryA.musculo || "—"}</div>
            <div>{comparison.summaryB.objetivo || "—"} · {comparison.summaryB.nivel || "—"} · {comparison.summaryB.musculo || "—"}</div>
          </div>
        ) : (
          <div className="plan-comparison-summary">
            <div>{comparison.summaryA.objective || "—"} · {comparison.summaryA.calorias || "—"} kcal</div>
            <div>{comparison.summaryB.objective || "—"} · {comparison.summaryB.calorias || "—"} kcal</div>
          </div>
        )}

        <div className="plan-comparison-rows">
          {comparison.rows.map((row, idx) => (
            <div className={`plan-comparison-row ${row.diff ? "plan-comparison-row--diff" : ""}`} key={idx}>
              <div className="plan-comparison-cell">
                {isRoutine ? fmtExercise(row.a) : fmtMeal(row.a)}
              </div>
              <div className="plan-comparison-cell">
                {isRoutine ? fmtExercise(row.b) : fmtMeal(row.b)}
              </div>
            </div>
          ))}
          {comparison.rows.length === 0 && (
            <p className="text-muted text-center py-3">{t("comparison.noDifferences")}</p>
          )}
        </div>
      </div>
    </div>
  );
}
