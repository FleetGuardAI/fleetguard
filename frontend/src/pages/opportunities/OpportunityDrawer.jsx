import { useEffect } from 'react';
import {
  X,
  MapPin,
  ArrowRight,
  User,
  Phone,
  Mail,
  FileText,
  IndianRupee,
  Clock,
  Calendar,
  Truck,
  Package,
  Weight,
  Route,
  AlertCircle,
  CheckCircle2,
  XCircle,
  MessageSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { PriorityBadge, StatusBadge, SourceBadge } from './OpportunityBadge';
import { OpportunityTimeline } from './OpportunityTimeline';
import { cn } from '@/utils/cn';

/**
 * Right-side drawer showing full opportunity details.
 * Slides in from the right with overlay backdrop.
 */
export function OpportunityDrawer({ opportunity, open, onClose, onAccept, onReject, onAssignTruck }) {
  const o = opportunity;

  // Lock body scroll when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
      const handleEsc = (e) => { if (e.key === 'Escape') onClose(); };
      document.addEventListener('keydown', handleEsc);
      return () => {
        document.removeEventListener('keydown', handleEsc);
        document.body.style.overflow = '';
      };
    }
    document.body.style.overflow = '';
  }, [open, onClose]);

  if (!open || !o) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />

      {/* Drawer panel */}
      <div
        className={cn(
          'relative w-full max-w-xl bg-surface border-l border-border shadow-2xl',
          'flex flex-col h-full',
          'animate-slide-in-right'
        )}
        style={{
          animation: 'slideInRight 0.3s ease-out forwards',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 pb-4 border-b border-border flex-shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-semibold text-content">{o.customer}</h2>
              <SourceBadge source={o.source} />
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-content-muted font-mono">{o.id}</span>
              <PriorityBadge priority={o.priority} />
              <StatusBadge status={o.status} />
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-surface-secondary transition-colors text-content-muted hover:text-content"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-6 space-y-6">
            {/* Route card */}
            <div className="rounded-xl bg-gradient-to-r from-brand-50 to-emerald-50 dark:from-brand-950/20 dark:to-emerald-950/20 border border-brand-100 dark:border-brand-900/30 p-4">
              <h4 className="text-xs font-semibold text-content-muted uppercase tracking-wider mb-3">
                Complete Route
              </h4>
              <div className="space-y-3">
                {/* Pickup */}
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center flex-shrink-0">
                    <MapPin className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-xs text-content-muted">Pickup</p>
                    <p className="text-sm font-semibold text-content">{o.pickup}</p>
                    <p className="text-xs text-content-secondary mt-0.5">{o.pickupAddress}</p>
                  </div>
                </div>

                {/* Connector */}
                <div className="flex items-center gap-3 pl-4">
                  <div className="w-px h-6 bg-border ml-[11px]" />
                  <ArrowRight className="h-3 w-3 text-content-muted" />
                  <span className="text-xs text-content-muted">{o.distance}</span>
                </div>

                {/* Drop */}
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center flex-shrink-0">
                    <MapPin className="h-4 w-4 text-red-600 dark:text-red-400" />
                  </div>
                  <div>
                    <p className="text-xs text-content-muted">Drop</p>
                    <p className="text-sm font-semibold text-content">{o.drop}</p>
                    <p className="text-xs text-content-secondary mt-0.5">{o.dropAddress}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Contact */}
            <Section title="Contact Person">
              <DetailRow icon={User} label="Name" value={o.contactName} />
              <DetailRow
                icon={Phone}
                label="Phone"
                value={o.phone}
                link={`tel:${o.phone}`}
              />
              <DetailRow
                icon={Mail}
                label="Email"
                value={o.email}
                link={`mailto:${o.email}`}
              />
              {o.broker && <DetailRow icon={User} label="Broker" value={o.broker} />}
            </Section>

            {/* Load details */}
            <Section title="Load Details">
              <DetailRow icon={Calendar} label="Pickup Date" value={formatDate(o.pickupDate)} />
              <DetailRow icon={Truck} label="Vehicle Required" value={o.vehicleType} />
              <DetailRow icon={Package} label="Load Type" value={o.loadType} />
              <DetailRow icon={Weight} label="Weight" value={o.weight} />
              <DetailRow icon={Route} label="Distance" value={o.distance} />
            </Section>

            {/* Cargo description */}
            {o.cargoDescription && (
              <Section title="Cargo Description">
                <p className="text-sm text-content-secondary leading-relaxed">
                  {o.cargoDescription}
                </p>
              </Section>
            )}

            {/* Special instructions */}
            {o.specialInstructions && (
              <Section title="Special Instructions">
                <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30">
                  <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-amber-800 dark:text-amber-300 leading-relaxed">
                    {o.specialInstructions}
                  </p>
                </div>
              </Section>
            )}

            {/* Payment */}
            <Section title="Payment Details">
              <DetailRow icon={IndianRupee} label="Expected Revenue" value={`₹${o.revenue?.toLocaleString('en-IN')}`} highlight />
              <DetailRow icon={IndianRupee} label="Advance Amount" value={o.advance ? `₹${o.advance.toLocaleString('en-IN')}` : 'None'} />
              <DetailRow icon={FileText} label="Payment Terms" value={o.paymentTerms} />
              <DetailRow icon={Clock} label="Expected Payment" value={o.expectedPaymentDays ? `${o.expectedPaymentDays} days` : 'On delivery'} />
            </Section>

            {/* Delivery timeline */}
            <Section title="Delivery Timeline">
              <p className="text-sm font-medium text-content">{o.deliveryTimeline}</p>
            </Section>

            {/* Documents */}
            {o.documents?.length > 0 && (
              <Section title="Documents">
                <div className="flex flex-wrap gap-2">
                  {o.documents.map((doc, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-surface-secondary border border-border rounded-lg text-content-secondary hover:border-brand-300 dark:hover:border-brand-700 transition-colors cursor-pointer"
                    >
                      <FileText className="h-3 w-3" />
                      {doc}
                    </span>
                  ))}
                </div>
              </Section>
            )}

            {/* Notes placeholder */}
            <Section title="Notes">
              {/* TODO: GET /api/opportunities/:id/notes */}
              <p className="text-sm text-content-muted italic">No notes added yet.</p>
            </Section>

            {/* Timeline activity */}
            <Section title="Activity Timeline">
              <OpportunityTimeline events={o.timeline || []} />
            </Section>
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex items-center gap-3 p-6 pt-4 border-t border-border flex-shrink-0 bg-surface">
          {o.status === 'available' && (
            <>
              <Button
                variant="danger"
                size="md"
                icon={<XCircle className="h-4 w-4" />}
                onClick={() => onReject?.(o.id)}
                className="flex-1"
              >
                Reject
              </Button>
              <Button
                variant="secondary"
                size="md"
                icon={<Truck className="h-4 w-4" />}
                onClick={() => onAssignTruck?.(o.id)}
                className="flex-1"
              >
                Assign Truck
              </Button>
              <Button
                variant="primary"
                size="md"
                icon={<CheckCircle2 className="h-4 w-4" />}
                onClick={() => onAccept?.(o.id)}
                className="flex-1"
              >
                Accept
              </Button>
            </>
          )}
          {o.status === 'accepted' && (
            <Button
              variant="secondary"
              size="md"
              icon={<Truck className="h-4 w-4" />}
              onClick={() => onAssignTruck?.(o.id)}
              className="flex-1"
            >
              Assign Truck
            </Button>
          )}
          {o.status === 'negotiating' && (
            <>
              <Button
                variant="secondary"
                size="md"
                icon={<MessageSquare className="h-4 w-4" />}
                onClick={() => {}}
                className="flex-1"
              >
                Continue Negotiation
              </Button>
              <Button
                variant="primary"
                size="md"
                icon={<CheckCircle2 className="h-4 w-4" />}
                onClick={() => onAccept?.(o.id)}
                className="flex-1"
              >
                Accept
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Inline animation style */}
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(100%); opacity: 0.9; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div>
      <h4 className="text-xs font-semibold text-content-muted uppercase tracking-wider mb-3">
        {title}
      </h4>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function DetailRow({ icon: Icon, label, value, link, highlight }) {
  const content = (
    <span className={cn(
      'text-sm',
      highlight ? 'font-bold text-brand-600 dark:text-brand-400' : 'text-content'
    )}>
      {value || '—'}
    </span>
  );

  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2 text-content-muted">
        <Icon className="h-3.5 w-3.5" strokeWidth={1.8} />
        <span className="text-xs">{label}</span>
      </div>
      {link ? (
        <a href={link} className="text-sm text-brand-600 dark:text-brand-400 hover:underline">
          {value}
        </a>
      ) : content}
    </div>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}
