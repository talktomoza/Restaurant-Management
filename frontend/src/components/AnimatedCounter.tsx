"use client";

import { useEffect, useState } from "react";

function parseNumeric(value: string): { prefix: string; number: number; suffix: string } {
  const match = value.match(/^([^\d-]*)([\d,.]+)(.*)$/);
  if (!match) return { prefix: "", number: 0, suffix: value };
  const [, prefix, numStr, suffix] = match;
  return { prefix, number: parseFloat(numStr.replace(/,/g, "")), suffix };
}

export default function AnimatedCounter({ value, durationMs = 900 }: { value: string; durationMs?: number }) {
  const [display, setDisplay] = useState(value);

  useEffect(() => {
    const { prefix, number, suffix } = parseNumeric(value);
    if (Number.isNaN(number)) {
      setDisplay(value);
      return;
    }
    const start = performance.now();
    let frame: number;

    function tick(now: number) {
      const progress = Math.min((now - start) / durationMs, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = number * eased;
      const formatted = suffix.includes("%")
        ? current.toFixed(1)
        : number % 1 !== 0
        ? current.toFixed(2)
        : Math.round(current).toLocaleString();
      setDisplay(`${prefix}${formatted}${suffix}`);
      if (progress < 1) frame = requestAnimationFrame(tick);
    }

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value, durationMs]);

  return <>{display}</>;
}
