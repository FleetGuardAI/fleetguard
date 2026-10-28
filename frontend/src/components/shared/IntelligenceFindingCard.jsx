import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert, AlertTriangle, AlertCircle, Info,
  CheckCircle2, ArrowUpRight, Truck, Wrench, Fuel,
  Compass, Database
} from 'lucide-react';
import { cn } from '@/utils/cn';

const CATEGORY_ICONS = {
  FLEET_HEALTH: ShieldAlert,
  FUEL_EFFICIENCY: Fuel,
  MAINTENANCE: Wrench,
  TRIP_OPERATIONS: Compass,
  DATA_QUALITY: Database
};

export default function IntelligenceFindingCard({ finding, onAction }) {
  const navigate = useNavigate();
  if (!finding) return null;

  const severity = (finding.severity || 'INFO').toUpperCase();
  const isCrit = severity === 'CRITICAL';
  const isHigh = severity === 'HIGH';
  const isMed = severity === 'MEDIUM';

  const categoryKey = (finding.category || 'FLEET_HEALTH').toUpperCase();
  const CategoryIcon = CATEGORY_ICONS[categoryKey] || ShieldAlert;

  const handleHandoff = () => {
    if (finding.action_handoff?.route) {
      navigate(finding.action_handoff.route);
    } else if (onAction) {
      onAction(finding);
    }
  };

  return (
    <div
      className={cn(
        "p-3.5 rounded-xl border text-content space-y-2.5 transition-all shadow-xs",
        isCrit ? "bg-rose-50/50 border-rose-200" :
        isHigh ? "bg-amber-50/50 border-amber-200" :
        isMed ? "bg-blue-50/40 border-blue-200" :
        "bg-surface border-border"
      )}
    >
      {/* Header Badges */}
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className={cn(
              "text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider border flex items-center gap-1",
              isCrit ? "bg-rose-100 text-rose-800 border-rose-300" :
              isHigh ? "bg-amber-100 text-amber-800 border-amber-300" :
              isMed ? "bg-blue-100 text-blue-800 border-blue-300" :
              "bg-slate-100 text-slate-700 border-slate-300"
            )}>
              {isCrit && <AlertTriangle className="w-2.5 h-2.5 text-rose-600 flex-shrink-0" />}
              {isHigh && <AlertCircle className="w-2.5 h-2.5 text-amber-600 flex-shrink-0" />}
              {isMed && <Info className="w-2.5 h-2.5 text-blue-600 flex-shrink-0" />}
              {severity}
            </span>

            <span className="text-[10px] font-medium text-content-muted uppercase flex items-center gap-1">
              <CategoryIcon className="w-3 h-3 text-content-muted" />
              {finding.category?.replace(/_/g, ' ')}
            </span>

            {finding.entity_name && (
              <span className="text-[11px] font-mono font-semibold text-content bg-white px-2 py-0.5 rounded border border-border/80 flex items-center gap-1 shadow-2xs">
                <Truck className="w-3 h-3 text-brand-500" />
                {finding.entity_name}
              </span>
            )}
          </div>

          <h4 className="text-xs font-bold text-content pt-0.5 leading-snug">
            {finding.title}
          </h4>
        </div>
      </div>

      {/* Summary Narrative */}
      <p className="text-xs text-content-secondary leading-relaxed">
        {finding.summary}
      </p>

      {/* Metrics & Baseline */}
      {(finding.measured_value || finding.baseline_value) && (
        <div className="grid grid-cols-2 gap-2 p-2 rounded-lg bg-surface/80 border border-border/60 text-[11px]">
          {finding.measured_value && (
            <div>
              <span className="text-[10px] text-content-muted uppercase tracking-wider block font-medium">Measured</span>
              <span className="font-semibold text-content">{finding.measured_value}</span>
            </div>
          )}
          {finding.baseline_value && (
            <div>
              <span className="text-[10px] text-content-muted uppercase tracking-wider block font-medium">Baseline / Target</span>
              <span className="text-content-secondary">{finding.baseline_value}</span>
            </div>
          )}
        </div>
      )}

      {/* Observation Period & Limitations */}
      <div className="space-y-1 text-[11px] text-content-muted border-t border-border/40 pt-2">
        {finding.observation_period && (
          <div className="text-[10px]">
            <span>Period: </span>
            <span className="font-medium text-content-secondary">{finding.observation_period}</span>
          </div>
        )}
        {finding.evidence_records?.length > 0 && (
          <div className="text-[10px] flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-500 flex-shrink-0" />
            <span className="truncate">Evidence: {finding.evidence_records.join('; ')}</span>
          </div>
        )}
      </div>

      {/* Recommended Action Box */}
      {finding.recommended_action && (
        <div className="text-xs text-brand-800 bg-brand-50/70 p-2.5 rounded-lg border border-brand-200/80 space-y-1 mt-1">
          <div className="flex items-start gap-1.5">
            <ArrowUpRight className="w-3.5 h-3.5 text-brand-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <strong className="font-semibold text-brand-900">Recommended Next Step: </strong>
              <span className="text-brand-800">{finding.recommended_action}</span>
            </div>
          </div>

          {finding.action_handoff && (
            <div className="pt-1 flex justify-end">
              <button
                type="button"
                onClick={handleHandoff}
                className="text-[11px] font-semibold text-brand-700 hover:text-brand-900 bg-white hover:bg-brand-50 px-2.5 py-1 rounded border border-brand-200 flex items-center gap-1 cursor-pointer transition-colors"
              >
                <span>{finding.action_handoff.action_label || 'View in Fleetguard'}</span>
                <ArrowUpRight className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Limitations note */}
      {finding.limitations && (
        <p className="text-[10px] text-content-muted italic px-0.5">
          Note: {finding.limitations}
        </p>
      )}
    </div>
  );
}
