import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  MapPin,
  Clock,
  AlertTriangle,
  Receipt,
  ChevronRight,
  Loader2,
} from 'lucide-react';

/**
 * Risk level badge component.
 * @param {{ level: string }} props
 */
function RiskBadge({ level }) {
  const config = {
    Low: 'bg-emerald-50 text-emerald-600 border-emerald-200',
    Medium: 'bg-amber-50 text-amber-600 border-amber-200',
    High: 'bg-red-50 text-red-600 border-red-200 risk-high',
    Critical: 'bg-red-100 text-red-700 border-red-300 risk-high',
  };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px]
      font-semibold uppercase tracking-wider border ${config[level] || config.Low}`}>
      {(level === 'High' || level === 'Critical') && (
        <AlertTriangle className="w-2.5 h-2.5" />
      )}
      {level}
    </span>
  );
}

/**
 * Time ago formatter.
 * @param {string} dateStr - ISO date string
 * @returns {string}
 */
function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/**
 * Action Queue — WhatsApp Ticket approval list.
 * @param {{ tickets: Array, onApprove: (id: number) => void, onReject: (id: number) => void }} props
 */
export default function ActionQueue({ tickets, onApprove, onReject }) {
  const [loadingId, setLoadingId] = useState(null);
  const pendingTickets = tickets?.filter((t) => t.status === 'pending') ?? [];
  const recentActions = tickets?.filter((t) => t.status !== 'pending')?.slice(0, 3) ?? [];

  const handleAction = async (id, action) => {
    setLoadingId(id);
    if (action === 'approve') {
      await onApprove?.(id);
    } else {
      await onReject?.(id);
    }
    setTimeout(() => setLoadingId(null), 500);
  };

  return (
    <div
      className="rounded-2xl dashboard-card p-5 animate-slide-up flex flex-col"
      style={{ animationDelay: '450ms', animationFillMode: 'both' }}
      id="action-queue"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-50">
            <Receipt className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Action Queue</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {pendingTickets.length} pending approval{pendingTickets.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <button className="text-xs text-emerald-600 hover:text-emerald-700 font-medium flex items-center gap-1 transition-colors">
          View All <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Pending Tickets */}
      <div className="space-y-3 flex-1 overflow-y-auto max-h-[400px] pr-1">
        {pendingTickets.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CheckCircle2 className="w-10 h-10 text-emerald-500/30 mb-3" />
            <p className="text-sm text-slate-400">All caught up!</p>
            <p className="text-xs text-slate-600 mt-1">No pending approvals</p>
          </div>
        )}

        {pendingTickets.map((ticket) => (
          <div
            key={ticket.id}
            className="group relative p-4 rounded-xl bg-white border border-slate-100
              hover:border-emerald-200 hover:shadow-sm transition-all duration-200"
          >
            <div className="flex items-start justify-between mb-2.5">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {ticket.driver_name}
                  </p>
                  <RiskBadge level={ticket.risk_level} />
                </div>
                <p className="text-xs text-slate-500">
                  {ticket.issue_type} · {ticket.truck_plate}
                </p>
              </div>
              <p className="text-lg font-bold text-slate-900 tabular-nums shrink-0 ml-3">
                ₹{ticket.amount?.toLocaleString('en-IN')}
              </p>
            </div>

            {/* Meta info */}
            <div className="flex items-center gap-4 mb-3 text-[11px] text-slate-500">
              {ticket.location_name && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {ticket.location_name}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {timeAgo(ticket.created_at)}
              </span>
            </div>

            {/* Fair price comparison */}
            {ticket.fair_price && ticket.amount > ticket.fair_price && (
              <div className="mb-3 px-2.5 py-1.5 rounded-lg bg-red-50 border border-red-100">
                <p className="text-[11px] text-red-600">
                  <AlertTriangle className="w-3 h-3 inline mr-1" />
                  Fair price: ₹{ticket.fair_price?.toLocaleString('en-IN')} ·
                  <span className="font-semibold">
                    {' '}{Math.round(((ticket.amount - ticket.fair_price) / ticket.fair_price) * 100)}% over
                  </span>
                </p>
              </div>
            )}

            {/* Duplicate warning */}
            {ticket.is_duplicate && (
              <div className="mb-3 px-2.5 py-1.5 rounded-lg bg-orange-50 border border-orange-100">
                <p className="text-[11px] text-orange-600 font-medium">
                  ⚠ Possible duplicate claim detected
                </p>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleAction(ticket.id, 'approve')}
                disabled={loadingId === ticket.id}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg
                  bg-emerald-600 hover:bg-emerald-700 border border-transparent
                  text-white text-xs font-semibold
                  transition-all duration-200 hover:shadow-md hover:shadow-emerald-500/20
                  disabled:opacity-50 disabled:cursor-not-allowed"
                id={`approve-${ticket.id}`}
              >
                {loadingId === ticket.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-3.5 h-3.5" />
                )}
                Approve & Pay
              </button>
              <button
                onClick={() => handleAction(ticket.id, 'reject')}
                disabled={loadingId === ticket.id}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg
                  bg-white hover:bg-red-50 border border-slate-200 hover:border-red-200
                  text-red-600 text-xs font-semibold
                  transition-all duration-200
                  disabled:opacity-50 disabled:cursor-not-allowed"
                id={`reject-${ticket.id}`}
              >
                <XCircle className="w-3.5 h-3.5" />
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Actions */}
      {recentActions.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-200">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold mb-2">
            Recent Actions
          </p>
          {recentActions.map((ticket) => (
            <div key={ticket.id} className="flex items-center justify-between py-1.5">
              <div className="flex items-center gap-2">
                {ticket.status === 'approved' ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                ) : (
                  <XCircle className="w-3.5 h-3.5 text-red-500" />
                )}
                <span className="text-xs text-slate-700">{ticket.driver_name}</span>
                <span className="text-xs text-slate-300">·</span>
                <span className="text-xs text-slate-500">{ticket.issue_type}</span>
              </div>
              <span className="text-xs font-medium text-slate-900 tabular-nums">
                ₹{ticket.amount?.toLocaleString('en-IN')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
