import React from 'react';

/**
 * Circular score gauge — CSS-only, no library dependency.
 * Shows the Trip Intelligence efficiency score as a ring.
 */
export function ScoreGauge({ score, maxScore = 100, size = 160, strokeWidth = 12, grade, label }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = score != null ? Math.min(score / maxScore, 1) : 0;
  const offset = circumference * (1 - pct);
  const hasData = score != null;

  const getColor = () => {
    if (!hasData) return '#94a3b8';
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#eab308';
    if (score >= 40) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background track */}
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-gray-200"
          />
          {/* Score arc */}
          {hasData && (
            <circle
              cx={size / 2} cy={size / 2} r={radius}
              fill="none" stroke={getColor()}
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1s ease-out' }}
            />
          )}
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {hasData ? (
            <>
              <span className="text-3xl font-bold text-content" style={{ color: getColor() }}>
                {Math.round(score)}
              </span>
              <span className="text-xs text-content-secondary">/ {maxScore}</span>
            </>
          ) : (
            <span className="text-xs text-content-muted text-center px-4">Score unavailable</span>
          )}
        </div>
      </div>
      {grade && (
        <span className="text-sm font-semibold" style={{ color: getColor() }}>{grade}</span>
      )}
      {label && <span className="text-xs text-content-secondary">{label}</span>}
    </div>
  );
}

/**
 * Horizontal stacked bar for cost breakdown.
 * Shows how revenue was consumed by different expense categories.
 */
const CATEGORY_COLORS = {
  FUEL: '#3b82f6',
  TOLL: '#8b5cf6',
  MAINTENANCE: '#f59e0b',
  PARKING: '#06b6d4',
  SALARY: '#10b981',
  ALLOWANCE: '#14b8a6',
  PENALTY: '#ef4444',
  LOADING: '#f97316',
  UNLOADING: '#d946ef',
  DRIVER_ADVANCE: '#0ea5e9',
  DETENTION: '#dc2626',
  MISCELLANEOUS: '#94a3b8',
};

export function CostBreakdownBar({ items, revenue }) {
  if (!items || items.length === 0) return null;

  const totalCost = items.reduce((sum, i) => sum + i.amount, 0);
  const profit = revenue != null ? revenue - totalCost : null;
  const baseWidth = revenue && revenue > 0 ? revenue : totalCost;

  return (
    <div className="space-y-3">
      {/* Revenue bar */}
      {revenue != null && (
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-content-secondary">Revenue</span>
            <span className="font-semibold text-content">₹{revenue.toLocaleString('en-IN')}</span>
          </div>
          <div className="h-6 rounded-md bg-green-100 border border-green-200" />
        </div>
      )}

      {/* Cost breakdown bar */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-content-secondary">Total Cost</span>
          <span className="font-semibold text-content">₹{totalCost.toLocaleString('en-IN')}</span>
        </div>
        <div className="h-6 rounded-md overflow-hidden flex" style={{ backgroundColor: '#f1f5f9' }}>
          {items.map((item, i) => (
            <div
              key={item.category}
              className="h-full relative group"
              style={{
                width: `${(item.amount / baseWidth) * 100}%`,
                backgroundColor: CATEGORY_COLORS[item.category] || '#94a3b8',
                minWidth: item.amount > 0 ? '2px' : '0',
              }}
              title={`${item.category_label}: ₹${item.amount.toLocaleString('en-IN')} (${item.percentage}%)`}
            >
              {/* Tooltip on hover */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block z-10">
                <div className="bg-gray-900 text-white text-[10px] px-2 py-1 rounded whitespace-nowrap shadow-lg">
                  {item.category_label}: ₹{item.amount.toLocaleString('en-IN')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Profit/Loss indicator */}
      {profit != null && (
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-content-secondary">{profit >= 0 ? 'Net Profit' : 'Net Loss'}</span>
            <span className={`font-bold ${profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {profit >= 0 ? '+' : ''}₹{profit.toLocaleString('en-IN')}
            </span>
          </div>
          <div
            className={`h-3 rounded-md ${profit >= 0
                ? 'bg-green-500'
                : 'bg-red-500'
              }`}
            style={{ width: `${Math.min(Math.abs(profit) / baseWidth * 100, 100)}%` }}
          />
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
        {items.map(item => (
          <div key={item.category} className="flex items-center gap-1.5 text-xs text-content-secondary">
            <span
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
              style={{ backgroundColor: CATEGORY_COLORS[item.category] || '#94a3b8' }}
            />
            <span>{item.category_label}</span>
            <span className="text-content-muted">({item.percentage}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Inline variance indicator bar.
 * Shows a centered zero-line with the variance extending left (favorable) or right (unfavorable).
 */
export function VarianceBar({ value, maxAbsValue = 50, severity = 'INFO', unit = '' }) {
  if (value == null) return <span className="text-xs text-content-muted">—</span>;

  const absVal = Math.abs(value);
  const pct = Math.min((absVal / maxAbsValue) * 50, 50);
  const isPositive = value > 0;
  const isNegative = value < 0;

  const barColor = severity === 'CRITICAL'
    ? 'bg-red-500'
    : severity === 'WARNING'
    ? 'bg-amber-500'
    : isNegative
    ? 'bg-green-500'
    : 'bg-blue-400';

  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="relative w-24 h-3 bg-gray-100 rounded-full overflow-hidden">
        {/* Center line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-300 z-10" />
        {/* Bar */}
        <div
          className={`absolute top-0 bottom-0 ${barColor} rounded-full`}
          style={{
            ...(isPositive
              ? { left: '50%', width: `${pct}%` }
              : { right: '50%', width: `${pct}%` }
            ),
            transition: 'width 0.5s ease-out',
          }}
        />
      </div>
      <span className={`text-xs font-medium whitespace-nowrap ${
        severity === 'CRITICAL' ? 'text-red-600' :
        severity === 'WARNING' ? 'text-amber-600' :
        'text-content-secondary'
      }`}>
        {isPositive ? '+' : ''}{value}{unit && ` ${unit}`}
      </span>
    </div>
  );
}

/**
 * Sub-score bar for efficiency breakdown.
 */
export function SubScoreBar({ label, score, maxScore = 100 }) {
  const pct = score != null ? (score / maxScore) * 100 : 0;
  const hasData = score != null;

  const getColor = () => {
    if (!hasData) return 'bg-gray-200';
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-amber-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-content-secondary">{label}</span>
        <span className="font-medium text-content">
          {hasData ? `${Math.round(score)}` : '—'}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
        <div
          className={`h-full rounded-full ${getColor()}`}
          style={{ width: `${pct}%`, transition: 'width 0.8s ease-out' }}
        />
      </div>
    </div>
  );
}
