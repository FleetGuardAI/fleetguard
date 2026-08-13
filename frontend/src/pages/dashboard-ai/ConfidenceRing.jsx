import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

/**
 * Animated SVG confidence circular indicator.
 */
export function ConfidenceRing({ percentage = 90, size = 48, strokeWidth = 3 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    // Animate stroke dashoffset based on percentage
    const progress = percentage / 100;
    const strokeOffset = circumference - progress * circumference;
    setOffset(strokeOffset);
  }, [percentage, circumference]);

  // Color map based on percentage
  const ringColor = percentage >= 90 
    ? 'text-emerald-500' 
    : percentage >= 75 
      ? 'text-amber-500' 
      : 'text-slate-400';

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="w-full h-full transform -rotate-90">
        {/* Track Ring */}
        <circle
          className="text-white/[0.06]"
          strokeWidth={strokeWidth}
          stroke="currentColor"
          fill="transparent"
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
        {/* Progress Ring */}
        <motion.circle
          className={ringColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          animate={{ strokeDashoffset: offset }}
          transition={{ type: 'spring', stiffness: 60, damping: 15 }}
          strokeLinecap="round"
          stroke="currentColor"
          fill="transparent"
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
      </svg>
      {/* Inner Label */}
      <span className="absolute text-[11px] font-bold tracking-tighter text-fg-text tabular-nums">
        {percentage}%
      </span>
    </div>
  );
}
