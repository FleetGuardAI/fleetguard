import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, TrendingUp, IndianRupee, Zap, ShieldCheck } from 'lucide-react';
import { cn } from '@/utils/cn';

const outcomes = [
  {
    icon: AlertTriangle,
    title: 'Detect issues earlier',
    desc: 'and reduce risk.',
  },
  {
    icon: TrendingUp,
    title: 'Improve operational',
    desc: 'efficiency.',
  },
  {
    icon: IndianRupee,
    title: 'Control costs and',
    desc: 'reduce leakage.',
  },
  {
    icon: Zap,
    title: 'Make faster,',
    desc: 'more informed decisions.',
  },
  {
    icon: ShieldCheck,
    title: 'Keep your fleet',
    desc: 'running profitably.',
  }
];

export function ProductAndOutcomesSection() {
  return (
    <section className="py-24 bg-surface text-content border-t border-border">
      <div className="container mx-auto px-6 max-w-7xl">
        
        <div className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-[10px] font-bold tracking-widest uppercase text-content-muted">Real Impact</span>
          </div>
          
          <h2 className="text-4xl md:text-5xl font-medium tracking-tight leading-[1.1] mb-6">
            Run a smarter,<br/>more profitable fleet.
          </h2>
        </div>

        {/* Business Outcomes */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6 pt-10 border-t border-border/50">
          {outcomes.map((outcome, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="flex flex-col items-center text-center group"
            >
              <div className="mb-4 text-content-secondary group-hover:scale-110 transition-transform duration-300">
                <outcome.icon className="w-8 h-8" strokeWidth={1.5} />
              </div>
              <h4 className="text-xs font-semibold text-content leading-tight">{outcome.title}</h4>
              <p className="text-[11px] text-content-muted leading-relaxed">{outcome.desc}</p>
            </motion.div>
          ))}
        </div>

      </div>
    </section>
  );
}
