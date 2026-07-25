import React, { useState, useMemo } from 'react';
import {
  Users,
  ChevronUp,
  ChevronDown,
  Star,
  Phone,
  TrendingUp,
  Shield,
  ArrowUpDown,
} from 'lucide-react';

/**
 * Risk score progress bar with color coding.
 * @param {{ score: number }} props
 */
function RiskBar({ score }) {
  const getColor = (s) => {
    if (s < 25) return { bar: 'bg-emerald-500', text: 'text-emerald-600', label: 'Low' };
    if (s < 50) return { bar: 'bg-amber-500', text: 'text-amber-600', label: 'Medium' };
    if (s < 75) return { bar: 'bg-orange-500', text: 'text-orange-600', label: 'High' };
    return { bar: 'bg-red-500', text: 'text-red-600', label: 'Critical' };
  };
  const color = getColor(score);

  return (
    <div className="flex items-center gap-3 min-w-[140px]">
      <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
        <div
          className={`h-full rounded-full ${color.bar} transition-all duration-700`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
      <span className={`text-xs font-bold tabular-nums ${color.text} w-7 text-right`}>
        {score}
      </span>
    </div>
  );
}

/**
 * Star rating display.
 * @param {{ rating: number }} props
 */
function StarRating({ rating }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`w-3 h-3 ${
            i <= Math.round(rating)
              ? 'text-amber-400 fill-amber-400'
              : 'text-slate-200'
          }`}
        />
      ))}
      <span className="text-xs text-slate-500 ml-1 tabular-nums">{rating != null ? Number(rating).toFixed(1) : 'N/A'}</span>
    </div>
  );
}

/**
 * Driver Risk & Performance Scoring Table.
 * @param {{ drivers: Array<{ id: number, name: string, phone_number: string, risk_score: number, rating: number, total_trips: number, total_expenses: number, is_active: boolean }> }} props
 */
export default function DriverTable({ drivers }) {
  const [sortKey, setSortKey] = useState('risk_score');
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === 'name');
    }
  };

  const sorted = useMemo(() => {
    if (!drivers?.length) return [];
    return [...drivers].sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];
      if (typeof valA === 'string') {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortAsc ? valA - valB : valB - valA;
    });
  }, [drivers, sortKey, sortAsc]);

  const SortIcon = ({ field }) => {
    if (sortKey !== field) return <ArrowUpDown className="w-3 h-3 text-slate-300" />;
    return sortAsc ? (
      <ChevronUp className="w-3.5 h-3.5 text-emerald-600" />
    ) : (
      <ChevronDown className="w-3.5 h-3.5 text-emerald-600" />
    );
  };

  const columns = [
    { key: 'name', label: 'Driver', width: 'w-[200px]' },
    { key: 'risk_score', label: 'Risk Score', width: 'w-[180px]' },
    { key: 'rating', label: 'Rating', width: 'w-[160px]' },
    { key: 'total_trips', label: 'Trips', width: 'w-[80px]' },
    { key: 'total_expenses', label: 'Total Expenses', width: 'w-[130px]' },
    { key: 'is_active', label: 'Status', width: 'w-[90px]' },
  ];

  return (
    <div
      className="rounded-2xl dashboard-card overflow-hidden animate-slide-up"
      style={{ animationDelay: '500ms', animationFillMode: 'both' }}
      id="driver-table"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-5 pb-0">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-violet-50">
            <Users className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Driver Risk & Performance</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {drivers?.length ?? 0} drivers · Sorted by {sortKey.replace('_', ' ')}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-slate-500" />
          <span className="text-[11px] text-slate-500">AI Risk Engine</span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto mt-4">
        <table className="w-full" id="driver-risk-table">
          <thead>
            <tr className="border-y border-slate-200">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`${col.width} px-5 py-3 text-left cursor-pointer
                    hover:bg-slate-50 transition-colors select-none`}
                  onClick={() => handleSort(col.key)}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold">
                      {col.label}
                    </span>
                    <SortIcon field={col.key} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((driver, idx) => (
              <tr
                key={driver.id}
                className="border-b border-slate-100 hover:bg-slate-50
                  transition-colors group cursor-pointer"
              >
                {/* Driver Name */}
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center
                      text-xs font-bold shrink-0
                      ${driver.risk_score >= 50
                        ? 'bg-gradient-to-br from-red-600 to-orange-600 text-white'
                        : 'bg-emerald-600 text-white'
                      }`}
                    >
                      {driver.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900 transition-colors">
                        {driver.name}
                      </p>
                      <p className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Phone className="w-2.5 h-2.5" />
                        {driver.phone_number}
                      </p>
                    </div>
                  </div>
                </td>

                {/* Risk Score */}
                <td className="px-5 py-3.5">
                  <RiskBar score={driver.risk_score} />
                </td>

                {/* Rating */}
                <td className="px-5 py-3.5">
                  <StarRating rating={driver.rating} />
                </td>

                {/* Trips */}
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-1.5">
                    <TrendingUp className="w-3 h-3 text-slate-400" />
                    <span className="text-sm text-slate-900 tabular-nums font-medium">
                      {driver.total_trips}
                    </span>
                  </div>
                </td>

                {/* Total Expenses */}
                <td className="px-5 py-3.5">
                  <span className="text-sm text-slate-900 tabular-nums font-medium">
                    ₹{driver.total_expenses?.toLocaleString('en-IN')}
                  </span>
                </td>

                {/* Status */}
                <td className="px-5 py-3.5">
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider
                    ${driver.is_active
                      ? 'bg-emerald-50 text-emerald-600'
                      : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${driver.is_active ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                    {driver.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-5 py-3 bg-slate-50 border-t border-slate-200">
        <p className="text-[11px] text-slate-500">
          Showing {sorted.length} of {drivers?.length ?? 0} drivers
        </p>
        <p className="text-[11px] text-slate-500">
          Flagged: {drivers?.filter((d) => d.risk_score > 50).length ?? 0} drivers
        </p>
      </div>
    </div>
  );
}
