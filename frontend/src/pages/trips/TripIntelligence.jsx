import React, { useState, useEffect } from 'react';
import { getTripIntelligence } from '@/api/tripApi';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';
import {
  ScoreGauge,
  CostBreakdownBar,
  VarianceBar,
  SubScoreBar,
} from './IntelligenceCharts';
import {
  TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Info,
  DollarSign, Fuel, Clock, MapPin, Target, BarChart3, History,
  Lightbulb, ChevronDown, ChevronUp, FileText,
} from 'lucide-react';
import './TripIntelligence.css';

/**
 * TripIntelligence — Main intelligence view for a single trip.
 * Displays financial summary, efficiency score, cost breakdown,
 * planned vs actual comparison, insights, and recommendations.
 */
export default function TripIntelligence({ tripId, trip }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedInsight, setExpandedInsight] = useState(null);

  useEffect(() => {
    loadIntelligence();
  }, [tripId]);

  const loadIntelligence = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getTripIntelligence(tripId);
      setData(result);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Intelligence Unavailable"
        message={error?.message || 'Could not load Trip Intelligence data.'}
        onRetry={loadIntelligence}
      />
    );
  }

  const { financial_summary: fs, efficiency_score: es } = data;

  return (
    <div className="ti-container space-y-6">
      {/* ══════ Data Quality Notice ══════ */}
      {data.data_quality === 'INSUFFICIENT' && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-amber-50 border border-amber-200">
          <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">Limited data available</p>
            <p className="text-xs text-amber-600 mt-1">
              Some intelligence sections may be incomplete. Add revenue, cost estimates, and expense records to get full analysis.
            </p>
          </div>
        </div>
      )}

      {/* ══════ Section 1: Financial Summary KPIs ══════ */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KPICard
          label="Revenue"
          value={fs.revenue}
          format="currency"
          icon={<DollarSign className="h-4 w-4" />}
          color="blue"
        />
        <KPICard
          label="Total Cost"
          value={fs.total_cost}
          format="currency"
          icon={<TrendingDown className="h-4 w-4" />}
          color="orange"
        />
        <KPICard
          label="Net Profit"
          value={fs.net_profit}
          format="currency"
          icon={fs.net_profit >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
          color={fs.net_profit != null ? (fs.net_profit >= 0 ? 'green' : 'red') : 'gray'}
        />
        <KPICard
          label="Profit Margin"
          value={fs.profit_margin_pct}
          format="percent"
          icon={<Target className="h-4 w-4" />}
          color={fs.profit_margin_pct != null ? (fs.profit_margin_pct >= 0 ? 'green' : 'red') : 'gray'}
        />
        <KPICard
          label="Cost / KM"
          value={fs.cost_per_km}
          format="currency"
          icon={<MapPin className="h-4 w-4" />}
          color="purple"
        />
        <KPICard
          label="Revenue / KM"
          value={fs.revenue_per_km}
          format="currency"
          icon={<BarChart3 className="h-4 w-4" />}
          color="teal"
        />
      </div>

      {/* ══════ Section 2: Efficiency Score + Why Underperform ══════ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Score Card */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4 text-brand-600" />
              Trip Intelligence Score
            </CardTitle>
          </CardHeader>
          <div className="flex flex-col items-center">
            <ScoreGauge
              score={es.overall_score}
              grade={es.grade}
              label="Trip Efficiency"
            />
            {es.explanation && (
              <p className="text-xs text-content-secondary mt-4 text-center max-w-xs">
                {es.explanation}
              </p>
            )}
            {/* Sub-scores */}
            {es.sub_scores && es.sub_scores.length > 0 && (
              <div className="w-full mt-5 space-y-2.5">
                {es.sub_scores.map(s => (
                  <SubScoreBar
                    key={s.name}
                    label={s.label}
                    score={s.has_data ? s.score : null}
                  />
                ))}
              </div>
            )}
          </div>
        </Card>

        {/* Why did this trip underperform? */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              {data.profit_loss_contributors.length > 0
                ? 'Why did this trip underperform?'
                : 'Trip Performance Summary'
              }
            </CardTitle>
          </CardHeader>

          {data.profit_loss_contributors.length > 0 ? (
            <div className="space-y-3">
              {data.profit_loss_contributors.map((c, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-lg bg-surface-secondary border border-border"
                >
                  <span className="ti-rank-badge flex-shrink-0">
                    {c.rank}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-content">{c.title}</span>
                      {c.is_estimate && (
                        <Badge variant="neutral" size="sm">Est.</Badge>
                      )}
                    </div>
                    <p className="text-xs text-content-secondary mt-0.5 line-clamp-2">
                      {c.description}
                    </p>
                  </div>
                  {c.impact_amount != null && (
                    <div className="flex-shrink-0 text-right">
                      <span className="text-sm font-bold text-red-600">
                        ₹{c.impact_amount.toLocaleString('en-IN')}
                      </span>
                      <p className="text-[10px] text-content-muted">impact</p>
                    </div>
                  )}
                </div>
              ))}

              {/* Total avoidable cost */}
              {data.profit_loss_contributors.some(c => c.impact_amount) && (
                <div className="flex justify-between items-center pt-2 border-t border-border">
                  <span className="text-xs font-medium text-content-secondary">
                    Estimated avoidable cost
                  </span>
                  <span className="text-sm font-bold text-red-600">
                    ₹{data.profit_loss_contributors
                      .reduce((sum, c) => sum + (c.impact_amount || 0), 0)
                      .toLocaleString('en-IN')}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center py-8 text-center">
              <CheckCircle className="h-10 w-10 text-green-500 mb-3" />
              <p className="text-sm font-medium text-content">No significant anomalies detected</p>
              <p className="text-xs text-content-secondary mt-1">
                {fs.has_sufficient_data
                  ? 'This trip performed within expected parameters.'
                  : 'Add more trip data (revenue, expenses) for deeper analysis.'
                }
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* ══════ Section 3: Cost Breakdown ══════ */}
      {data.cost_breakdown.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-brand-600" />
              Cost Breakdown — Where did the money go?
            </CardTitle>
          </CardHeader>
          <CostBreakdownBar items={data.cost_breakdown} revenue={fs.revenue} />
        </Card>
      )}

      {/* ══════ Section 4: Planned vs Actual ══════ */}
      {data.planned_vs_actual.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4 text-brand-600" />
              Planned vs Actual
            </CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 text-xs font-medium text-content-secondary">Metric</th>
                  <th className="text-right py-2 text-xs font-medium text-content-secondary">Planned</th>
                  <th className="text-right py-2 text-xs font-medium text-content-secondary">Actual</th>
                  <th className="text-right py-2 text-xs font-medium text-content-secondary">Variance</th>
                  <th className="py-2 text-xs font-medium text-content-secondary pl-4">Indicator</th>
                </tr>
              </thead>
              <tbody>
                {data.planned_vs_actual.map((item) => (
                  <tr key={item.metric} className="border-b border-border/50 last:border-0">
                    <td className="py-3 font-medium text-content">{item.metric_label}</td>
                    <td className="py-3 text-right text-content-secondary">
                      {item.planned != null
                        ? `${item.unit === '₹' ? '₹' : ''}${item.planned.toLocaleString('en-IN')}${item.unit !== '₹' ? ` ${item.unit}` : ''}`
                        : '—'}
                    </td>
                    <td className="py-3 text-right font-medium text-content">
                      {item.actual != null
                        ? `${item.unit === '₹' ? '₹' : ''}${item.actual.toLocaleString('en-IN')}${item.unit !== '₹' ? ` ${item.unit}` : ''}`
                        : '—'}
                    </td>
                    <td className="py-3 text-right">
                      {item.has_data && item.variance_pct != null ? (
                        <span className={`text-xs font-medium ${
                          item.severity === 'CRITICAL' ? 'text-red-600' :
                          item.severity === 'WARNING' ? 'text-amber-600' :
                          'text-content-secondary'
                        }`}>
                          {item.variance_pct > 0 ? '+' : ''}{item.variance_pct}%
                        </span>
                      ) : (
                        <span className="text-xs text-content-muted">—</span>
                      )}
                    </td>
                    <td className="py-3 pl-4">
                      {item.has_data ? (
                        <VarianceBar
                          value={item.variance_pct}
                          severity={item.severity}
                          unit="%"
                        />
                      ) : (
                        <span className="text-xs text-content-muted">Insufficient data</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ══════ Section 5: Intelligence Insights ══════ */}
      {data.insights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-brand-600" />
              Intelligence Insights
            </CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {data.insights.map((insight, i) => (
              <InsightCard
                key={i}
                insight={insight}
                isExpanded={expandedInsight === i}
                onToggle={() => setExpandedInsight(expandedInsight === i ? null : i)}
              />
            ))}
          </div>
        </Card>
      )}

      {/* ══════ Section 6: Historical Comparisons ══════ */}
      {data.historical_comparisons.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <History className="h-4 w-4 text-brand-600" />
              Historical Comparison
            </CardTitle>
          </CardHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.historical_comparisons.map((comp, i) => (
              <div key={i} className="p-3 rounded-lg bg-surface-secondary border border-border">
                <p className="text-xs text-content-secondary mb-2">{comp.metric_label}</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-lg font-bold text-content">
                    {comp.unit === '₹' ? '₹' : ''}{comp.current_value?.toLocaleString('en-IN')}
                    {comp.unit !== '₹' ? ` ${comp.unit}` : ''}
                  </span>
                  {comp.variance_pct != null && (
                    <Badge
                      variant={comp.is_favorable ? 'success' : 'danger'}
                      size="sm"
                    >
                      {comp.variance_pct > 0 ? '+' : ''}{comp.variance_pct}%
                    </Badge>
                  )}
                </div>
                <p className="text-[11px] text-content-muted mt-1">
                  vs {comp.unit === '₹' ? '₹' : ''}{comp.comparison_value?.toLocaleString('en-IN')}
                  {comp.unit !== '₹' ? ` ${comp.unit}` : ''} — {comp.comparison_label}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ══════ Section 7: Recommendations ══════ */}
      {data.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-brand-600" />
              Recommended Actions
            </CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {data.recommendations.map((rec, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-surface-secondary transition-colors">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-brand-100 text-brand-700 text-xs font-bold flex-shrink-0">
                  {rec.priority}
                </span>
                <div>
                  <p className="text-sm font-medium text-content">{rec.title}</p>
                  <p className="text-xs text-content-secondary mt-0.5">{rec.description}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ══════ Data Sources Footer ══════ */}
      <div className="flex items-center gap-2 text-[10px] text-content-muted pt-2">
        <FileText className="h-3 w-3" />
        <span>Data sources: {data.data_sources_used.join(', ')}</span>
        <span className="mx-1">•</span>
        <span>Data quality: {data.data_quality}</span>
      </div>
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════
   Sub-Components
   ═══════════════════════════════════════════════════════════════ */

function KPICard({ label, value, format, icon, color = 'gray' }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    teal: 'bg-teal-50 text-teal-600 border-teal-200',
    gray: 'bg-gray-50 text-gray-600 border-gray-200',
  };

  const formatValue = () => {
    if (value == null) return '—';
    if (format === 'currency') return `₹${value.toLocaleString('en-IN')}`;
    if (format === 'percent') return `${value}%`;
    return value.toLocaleString('en-IN');
  };

  return (
    <div className={`rounded-xl border p-3 ${colorClasses[color]}`}>
      <div className="flex items-center gap-1.5 mb-1.5 opacity-80">
        {icon}
        <span className="text-[10px] font-medium uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-lg font-bold leading-tight">
        {formatValue()}
      </p>
    </div>
  );
}


function InsightCard({ insight, isExpanded, onToggle }) {
  const severityConfig = {
    CRITICAL: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      icon: <AlertTriangle className="h-4 w-4 text-red-500" />,
      badge: 'danger',
    },
    WARNING: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      icon: <AlertTriangle className="h-4 w-4 text-amber-500" />,
      badge: 'warning',
    },
    INFO: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      icon: <Info className="h-4 w-4 text-blue-500" />,
      badge: 'info',
    },
  };

  const config = severityConfig[insight.severity] || severityConfig.INFO;

  return (
    <div className={`rounded-lg border ${config.border} ${config.bg} overflow-hidden`}>
      <button
        className="w-full flex items-start gap-3 p-3 text-left"
        onClick={onToggle}
      >
        <span className="flex-shrink-0 mt-0.5">{config.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-content">{insight.title}</span>
            <Badge variant={config.badge} size="sm">{insight.severity}</Badge>
            {insight.impact_amount != null && (
              <span className="text-xs font-semibold text-red-600">
                ₹{insight.impact_amount.toLocaleString('en-IN')} impact
                {insight.is_estimate && ' (est.)'}
              </span>
            )}
          </div>
          <p className="text-xs text-content-secondary mt-1">{insight.description}</p>
        </div>
        <span className="flex-shrink-0 text-content-muted">
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </span>
      </button>

      {/* Evidence panel */}
      {isExpanded && insight.evidence && insight.evidence.length > 0 && (
        <div className="border-t border-border/50 px-3 py-2.5 space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-content-muted">Evidence</p>
          {insight.evidence.map((ev, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <FileText className="h-3 w-3 text-content-muted flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-medium text-content">{ev.label}</span>
                {ev.detail && (
                  <span className="text-content-secondary ml-1">— {ev.detail}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
