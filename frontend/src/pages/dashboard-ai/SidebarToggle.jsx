import React from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/utils/cn';

/**
 * Premium collapsible sidebar toggle trigger button with spring physics.
 */
export function SidebarToggle({ collapsed, onClick, className }) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={cn(
        'w-6 h-6 rounded-full bg-white border border-border shadow-elevated',
        'flex items-center justify-center text-content-muted hover:text-brand-500',
        'transition-colors duration-200 cursor-pointer focus:outline-none',
        className
      )}
    >
      <motion.div
        animate={{ rotate: collapsed ? 180 : 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 18 }}
      >
        <ChevronLeft className="w-3.5 h-3.5" />
      </motion.div>
    </motion.button>
  );
}
