import React from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, Fuel, BellRing, CheckSquare, 
  BarChart3, Sparkles, Users, ArrowRight 
} from 'lucide-react';
import { cn } from '@/utils/cn';

const engines = [
  {
    id: 'trip',
    name: 'Trip Intelligence',
    desc: 'Understand trip economics, efficiency, and profitability.',
    icon: TrendingUp,
    color: 'text-emerald-500'
  },
  {
    id: 'fuel',
    name: 'Fuel Intelligence',
    desc: 'Detect anomalies and control fuel costs.',
    icon: Fuel,
    color: 'text-orange-500'
  },
  {
    id: 'signal',
    name: 'Signal Deck',
    desc: 'Find what actually needs your attention.',
    icon: BellRing,
    color: 'text-red-500'
  },
  {
    id: 'verify',
    name: 'Verification',
    desc: 'Cross-check expenses, receipts, and events.',
    icon: CheckSquare,
    color: 'text-blue-500'
  },
  {
    id: 'ops',
    name: 'Operations Engine',
    desc: 'See the business impact across your fleet.',
    icon: BarChart3,
    color: 'text-indigo-500'
  },
  {
    id: 'copilot',
    name: 'AI Copilot',
    desc: 'Ask questions. Get context. Take action.',
    icon: Sparkles,
    color: 'text-purple-500'
  }
];

export function EnginesSection() {
  return (
    <section className="py-24 bg-surface-secondary text-content border-t border-border">
      <div className="container mx-auto px-6 max-w-6xl">
        <div className="flex flex-col lg:flex-row gap-12 xl:gap-20 items-start relative">
          
          {/* Text Content - Sticky Left */}
          <div className="w-full lg:w-[35%] space-y-6 lg:sticky lg:top-32 shrink-0">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-[2px] bg-fg-green"></div>
              <span className="text-xs font-bold tracking-widest uppercase text-content-muted">Intelligence Engines</span>
            </div>
            
            <h2 className="text-4xl md:text-5xl font-medium tracking-tight leading-[1.1]">
              Different perspectives.<br/>
              <span className="text-fg-green">One connected system.</span>
            </h2>
            
            <p className="text-lg text-content-secondary font-light leading-relaxed">
              <strong>the vaahan</strong> is the intelligence platform. Inside it are different engines — each looking at your fleet from a different angle, but working together to give you a complete understanding.
            </p>

            <div className="pt-4 flex items-center text-sm font-medium text-fg-green hover:text-fg-green-deep transition-colors cursor-pointer group w-max">
              See all capabilities
              <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Engines Grid - Scrolling Right */}
          <div className="w-full lg:w-[65%]">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 md:gap-6">
              {engines.map((engine, index) => (
                <motion.div
                  key={engine.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-100px" }}
                  transition={{ delay: (index % 2) * 0.1, duration: 0.5 }}
                  className="bg-white border border-border p-8 rounded-2xl hover:shadow-lg hover:border-fg-green/20 transition-all duration-300 group flex flex-col h-full"
                >
                  <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center mb-6 border transition-colors duration-300", 
                    engine.color.replace('text-', 'bg-').replace('500', '50'),
                    engine.color.replace('text-', 'border-').replace('500', '100'),
                    "group-hover:bg-white"
                  )}>
                    <engine.icon className={cn("w-6 h-6 transition-colors duration-300", engine.color)} strokeWidth={1.5} />
                  </div>
                  <h3 className="text-lg font-semibold text-content mb-3 tracking-tight group-hover:text-fg-green transition-colors">{engine.name}</h3>
                  <p className="text-[15px] text-content-muted font-light leading-relaxed flex-1">{engine.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
