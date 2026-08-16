import {
  MapPin,
  ArrowRight,
  Calendar,
  Truck,
  Package,
  Weight,
  Route,
  IndianRupee,
  Clock,
  Eye,
  CheckCircle2,
  MessageSquare,
  XCircle,
  MoreHorizontal,
  User,
  Phone,
  Copy,
  Flag,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Dropdown } from '@/components/ui/Dropdown';
import { PriorityBadge, StatusBadge, SourceBadge } from './OpportunityBadge';
import { cn } from '@/utils/cn';

/**
 * Individual opportunity card displayed in the feed grid.
 * Premium card design with hover effects, route visualization, and quick actions.
 */
export function OpportunityCard({ opportunity, onViewDetails, onAccept, onNegotiate, onReject, index = 0 }) {
  const o = opportunity;

  const moreMenuItems = [
    { icon: <Copy className="h-4 w-4" />, label: 'Copy ID', onClick: () => navigator.clipboard?.writeText(o.id) },
    { icon: <Phone className="h-4 w-4" />, label: 'Call Contact', onClick: () => window.open(`tel:${o.phone}`) },
    { icon: <Flag className="h-4 w-4" />, label: 'Flag Issue', onClick: () => {} },
    { divider: true },
    { icon: <XCircle className="h-4 w-4" />, label: 'Reject', onClick: () => onReject?.(o.id), danger: true },
  ];

  return (
    <div
      className={cn(
        'group relative bg-surface border border-border rounded-2xl overflow-hidden',
        'transition-all duration-300',
        'hover:shadow-elevated hover:-translate-y-1 hover:border-brand-200:border-brand-800/50',
        'animate-slide-up',
        o.status === 'expired' && 'opacity-60'
      )}
      style={{ animationDelay: `${index * 60}ms`, animationFillMode: 'both' }}
    >
      {/* Priority accent strip */}
      <div
        className={cn(
          'h-1 w-full',
          o.priority === 'high' && 'bg-gradient-to-r from-red-500 to-orange-500',
          o.priority === 'medium' && 'bg-gradient-to-r from-amber-400 to-yellow-500',
          o.priority === 'low' && 'bg-gradient-to-r from-emerald-400 to-green-500'
        )}
      />

      <div className="p-5">
        {/* Header: Avatar + Customer + Badges */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3 min-w-0">
            {/* Customer avatar */}
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-100 to-brand-200 flex items-center justify-center flex-shrink-0 border border-brand-200/50">
              <span className="text-sm font-bold text-brand-700">
                {o.customer.charAt(0)}
              </span>
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-content truncate">
                {o.customer}
              </h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs text-content-muted font-mono">{o.id}</span>
                <SourceBadge source={o.source} />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
            <PriorityBadge priority={o.priority} />
            <StatusBadge status={o.status} />
          </div>
        </div>

        {/* Route visualization */}
        <div className="flex items-center gap-2 mb-4 px-3 py-2.5 rounded-xl bg-surface-secondary border border-border/50">
          <div className="flex items-center gap-1.5 min-w-0">
            <div className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0" />
            <span className="text-sm font-medium text-content truncate">{o.pickup}</span>
          </div>
          <div className="flex items-center gap-1 flex-shrink-0 text-content-muted">
            <div className="w-8 h-px bg-content-muted/30" />
            <ArrowRight className="h-3.5 w-3.5" />
            <div className="w-8 h-px bg-content-muted/30" />
          </div>
          <div className="flex items-center gap-1.5 min-w-0">
            <div className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />
            <span className="text-sm font-medium text-content truncate">{o.drop}</span>
          </div>
        </div>

        {/* Info grid */}
        <div className="grid grid-cols-2 gap-2.5 mb-4">
          <InfoChip icon={Calendar} label="Pickup" value={formatDate(o.pickupDate)} />
          <InfoChip icon={Truck} label="Vehicle" value={o.vehicleType} />
          <InfoChip icon={Package} label="Load" value={o.loadType} />
          <InfoChip icon={Weight} label="Weight" value={o.weight} />
          <InfoChip icon={Route} label="Distance" value={o.distance} />
          <InfoChip icon={Clock} label="Posted" value={formatTimeAgo(o.postedAt)} />
        </div>

        {/* Broker */}
        {o.broker && (
          <div className="flex items-center gap-1.5 mb-4 text-xs text-content-muted">
            <User className="h-3.5 w-3.5" />
            <span>via <span className="font-medium text-content-secondary">{o.broker}</span></span>
          </div>
        )}

        {/* Footer: Revenue + Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-border/50">
          <div>
            <p className="text-xs text-content-muted uppercase tracking-wider mb-0.5">Revenue</p>
            <p className="text-lg font-bold text-content flex items-center">
              <IndianRupee className="h-4 w-4 mr-0.5" />
              {o.revenue.toLocaleString('en-IN')}
            </p>
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onViewDetails?.(o)}
              className="opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            >
              <Eye className="h-3.5 w-3.5 mr-1" />
              View
            </Button>

            {o.status === 'available' && (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onNegotiate?.(o.id)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                >
                  <MessageSquare className="h-3.5 w-3.5 mr-1" />
                  Negotiate
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onAccept?.(o.id)}
                >
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                  Accept
                </Button>
              </>
            )}

            <Dropdown
              align="right"
              trigger={
                <button className="p-1.5 rounded-lg hover:bg-surface-secondary transition-colors text-content-muted hover:text-content">
                  <MoreHorizontal className="h-4 w-4" />
                </button>
              }
              items={moreMenuItems}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Small info chip used in the card's detail grid.
 */
function InfoChip({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-surface-secondary/60">
      <Icon className="h-3.5 w-3.5 text-content-muted flex-shrink-0" strokeWidth={1.8} />
      <div className="min-w-0">
        <p className="text-[10px] text-content-muted uppercase tracking-wider leading-none mb-0.5">{label}</p>
        <p className="text-xs font-medium text-content truncate">{value}</p>
      </div>
    </div>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return '—';
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return 'Just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return formatDate(dateStr);
}
