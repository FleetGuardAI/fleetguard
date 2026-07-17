import React from 'react';
import { motion } from 'framer-motion';
import { Clock, HelpCircle, Activity } from 'lucide-react';

/**
 * Clean, spring-animated timeline used within the expanded Signal Panel.
 */
export function SignalTimeline({ events = [] }) {
  if (!events || events.length === 0) {
    return (
      <div className="text-xs text-content-muted italic py-2 flex items-center gap-1.5">
        <HelpCircle className="w-3.5 h-3.5" />
        No historical log recorded.
      </div>
    );
  }

  return (
    <div className="relative pl-4 border-l border-border/40 space-y-4">
      {events.map((event, i) => (
        <motion.div
          key={event.id || i}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20, delay: i * 0.1 }}
          className="relative text-xs leading-relaxed"
        >
          {/* Circular Indicator Dot */}
          <div className="absolute left-[-21.5px] top-[4px] w-2.5 h-2.5 rounded-full bg-slate-900 dark:bg-white border-2 border-slate-300 dark:border-slate-800 flex-shrink-0" />
          
          <div className="flex items-center gap-2 mb-0.5">
            <span className="font-semibold text-content">{event.user || 'System Diagnostics'}</span>
            <span className="text-[10px] text-content-muted flex items-center gap-0.5">
              <Clock className="w-3 h-3" />
              {formatTime(event.timestamp)}
            </span>
          </div>
          <p className="text-content-secondary">{event.message}</p>
        </motion.div>
      ))}
    </div>
  );
}

function formatTime(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
  });
}
