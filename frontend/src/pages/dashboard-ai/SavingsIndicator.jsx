import React, { useEffect, useState } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';

/**
 * Animated Savings counter with soft radial glow effect on mount/value change.
 */
export function SavingsIndicator({ value = 0 }) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (latest) => {
    return Math.round(latest).toLocaleString('en-IN');
  });

  const [glowing, setGlowing] = useState(true);

  useEffect(() => {
    // Soft count-up animation
    const controls = animate(count, value, {
      duration: 1.6,
      ease: [0.16, 1, 0.3, 1], // premium out-expo
    });

    // Trigger glow pulse
    setGlowing(true);
    const timer = setTimeout(() => setGlowing(false), 2000);

    return () => {
      controls.stop();
      clearTimeout(timer);
    };
  }, [value, count]);

  return (
    <div className="relative inline-flex items-baseline">
      {/* Soft background glow */}
      <span className="text-2xl md:text-3xl font-light text-content tracking-tight select-none relative z-10 flex items-center">
        <span className="text-lg font-medium text-content-muted mr-1">₹</span>
        <motion.span className="font-semibold">{rounded}</motion.span>
        
        {/* Ambient indicator glow */}
        <motion.span
          animate={{
            opacity: glowing ? 0.15 : 0,
            scale: glowing ? 1.1 : 0.95,
          }}
          transition={{ duration: 1.2 }}
          className="absolute inset-0 bg-brand-500 blur-xl rounded-lg -z-10"
        />
      </span>
    </div>
  );
}
