import { useEffect, useRef, useState } from "react";

/* =========================================================
   useCountUp — animates a numeric value from 0 to `target`
   Adapted from the data-target stat-counter in kimi_ui_reference.html

   @param {number} target    Final value to count to
   @param {number} duration  Animation duration in ms (default 2000)
   @param {number} decimals  Decimal places to show (default 0)
   @param {boolean} start    Set to true to begin animation (default true)
   @returns {string} formatted current value
   ========================================================= */

export function useCountUp(target, duration = 2000, decimals = 0, start = true) {
  const [value, setValue] = useState("0");
  const rafRef = useRef(null);

  useEffect(() => {
    if (!start) return;

    const numTarget = parseFloat(target) || 0;
    let startTime = null;

    function update(now) {
      if (!startTime) startTime = now;
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Cubic ease-out
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = numTarget * eased;

      if (decimals > 0) {
        setValue(current.toFixed(decimals));
      } else {
        setValue(Math.floor(current).toLocaleString());
      }

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(update);
      } else {
        // Ensure final value is exact
        setValue(
          decimals > 0
            ? numTarget.toFixed(decimals)
            : numTarget.toLocaleString()
        );
      }
    }

    rafRef.current = requestAnimationFrame(update);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration, decimals, start]);

  return value;
}
