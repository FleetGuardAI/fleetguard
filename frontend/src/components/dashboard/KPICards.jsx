import React from 'react';
import { Truck, Navigation, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function KPICards() {
  const cards = [
    {
      label: 'ACTIVE TRUCKS',
      value: 148,
      icon: Truck,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      trend: '+12 today',
      sparkline: [20, 25, 23, 28, 35, 32, 40]
    },
    {
      label: 'EN-ROUTE',
      value: 112,
      icon: Navigation,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      trend: 'On-schedule',
      sparkline: [15, 18, 22, 21, 25, 28, 30]
    },
    {
      label: 'MAINTENANCE',
      value: 18,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
      trend: '2 scheduled',
      sparkline: [5, 4, 3, 5, 4, 3, 2]
    },
    {
      label: 'VERIFICATION RATE',
      value: '98.4%',
      icon: ShieldCheck,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      trend: '+1.2% increase',
      sparkline: [92, 94, 95, 96, 98, 97, 98.4]
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" id="kpi-cards">
      {cards.map((card, i) => {
        const Icon = card.icon;
        
        return (
          <div
            key={i}
            className="p-4 rounded-xl dashboard-card flex items-center justify-between"
          >
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-slate-500 tracking-wider uppercase">
                {card.label}
              </span>
              <p className="text-2xl font-extrabold text-slate-900">{card.value}</p>
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-slate-500">{card.trend}</span>
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              <div className={`p-2 rounded-lg ${card.bgColor} ${card.color}`}>
                <Icon className="w-4 h-4" />
              </div>
              
              {/* Thin bright line for sparkline representation */}
              <svg className="w-14 h-6 opacity-80" viewBox="0 0 100 30">
                <polyline
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  className={card.color}
                  points={card.sparkline.map((val, idx) => `${idx * 16},${30 - (val / 4)}`).join(' ')}
                />
              </svg>
            </div>
          </div>
        );
      })}
    </div>
  );
}
