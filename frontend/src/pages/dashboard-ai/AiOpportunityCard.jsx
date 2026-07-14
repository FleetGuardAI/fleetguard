import { useState, useRef } from 'react';
import {
  Sparkles,
  Search,
  UserPlus,
  CalendarClock,
  XCircle,
  TrendingUp,
  Clock,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
  ShieldAlert,
  Flame,
  CheckCircle,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { SEVERITY_CONFIG } from '@/data/aiOpportunityData';

/**
 * Conversational text explaining the insight.
 */
function getConversationalNarrative(o) {
  const truckPlate = o.truck ? `**${o.truck.plate}**` : '';
  const driverName = o.driver ? `**${o.driver.name}**` : '';
  const savingFormatted = `**₹${o.potentialSaving.toLocaleString('en-IN')}**`;

  switch (o.category) {
    case 'fuel_waste':
      return (
        <span>
          Fuel efficiency dropped on truck {truckPlate} (driven by {driverName}). 
          Fuel economy fell from 4.8 km/L to 3.9 km/L. This is costing you 
          roughly {savingFormatted} per month. We recommend inspecting tyres and injectors.
        </span>
      );
    case 'unused_truck':
      return (
        <span>
          Truck {truckPlate} has been sitting idle at the yard for 6 days. Leaving this vehicle 
          unassigned is causing fixed depreciation leakage of about {savingFormatted} this month. 
          Suggest assigning to the pending Jaipur-Mumbai route.
        </span>
      );
    case 'driver_behaviour':
      return (
        <span>
          Detected 3 harsh braking events from driver {driverName} while operating {truckPlate} on NH-48. 
          This aggressive style is accelerating brake wear, costing {savingFormatted} in unexpected maintenance.
        </span>
      );
    case 'route_optimization':
      return (
        <span>
          Found a more cost-effective alternative for the Ahmedabad → Delhi corridor. Routing truck {truckPlate} via 
          the Udaipur bypass instead of NH-48 direct will save {savingFormatted} per round trip.
        </span>
      );
    case 'delayed_payment':
      return (
        <span>
          Customer **Bharat Traders** has a total outstanding balance of **₹2.4L** that is now more than 45 days overdue. 
          This delays your cash flow and costs you {savingFormatted} in working capital interest.
        </span>
      );
    case 'high_maintenance':
      return (
        <span>
          Maintenance expenses for {truckPlate} spiked to 2.3x the fleet average, totaling ₹67,200 this quarter. 
          Investigating driver {driverName}'s clutch handling could save you up to {savingFormatted}.
        </span>
      );
    case 'insurance_renewal':
      return (
        <span>
          The insurance policy for {truckPlate} is expiring in 18 days. Renewing before 20 Jul locks in 
          an early renewal discount, saving you {savingFormatted} on the premium.
        </span>
      );
    case 'permit_expiry':
      return (
        <span>
          The national permit for truck {truckPlate} expires in 12 days. Operating without this permit carries a fine of 
          ₹5,000. Renewing online today prevents {savingFormatted} in fines and delays.
        </span>
      );
    case 'customer_profitability':
      return (
        <span>
          Operating trips for customer **Apex Logistics** is currently unprofitable, resulting in a net loss of 
          **₹12,000 per trip**. Renegotiating rates will save you {savingFormatted} this month.
        </span>
      );
    case 'invoice_delay':
      return (
        <span>
          There are 4 completed trips that have been pending invoice generation for over 7 days. Auto-generating 
          and sending these invoices now will save you {savingFormatted} in cash cycles.
        </span>
      );
    case 'low_driver_rating':
      return (
        <span>
          Driver {driverName}'s average rating fell to 3.2 this month following complaints. Mandating 
          a 2-day rest period to prevent fatigue will save {savingFormatted} in potential contract penalties.
        </span>
      );
    case 'unexpected_expense':
      return (
        <span>
          We flagged an unexpected clutch repair bill of **₹22,000** for truck {truckPlate}. Since the clutch was replaced 
          just 2 months ago, filing a warranty claim will recover {savingFormatted} of this cost.
        </span>
      );
    case 'emergency_cash':
      return (
        <span>
          Driver {driverName} requested an emergency cash advance of **₹5,000** at 2:30 AM from Sirohi. Approving a 
          partial advance of ₹3,000 while requesting receipts will save {savingFormatted} in unverified cash outflow.
        </span>
      );
    case 'duplicate_fuel':
      return (
        <span>
          Caught a potential duplicate fuel transaction of {savingFormatted} submitted by driver {driverName} at Barmer. 
          Rejecting this duplicate will prevent double-payment.
        </span>
      );
    case 'idle_time':
      return (
        <span>
          Truck {truckPlate} is averaging 4.2 hours of idle time per day (68% above fleet norms). Adjusting departure 
          schedules to align with warehouse slots will save {savingFormatted} monthly.
        </span>
      );
    default:
      return <span>{o.title}. {o.recommendation} Potential savings: {savingFormatted}.</span>;
  }
}

function getPrimaryActionLabel(category) {
  switch (category) {
    case 'fuel_waste':
    case 'high_maintenance':
    case 'unexpected_expense':
      return 'Inspect Vehicle';
    case 'unused_truck':
      return 'Schedule Route';
    case 'driver_behaviour':
    case 'low_driver_rating':
      return 'Alert Driver';
    case 'route_optimization':
      return 'Apply Bypass';
    case 'delayed_payment':
    case 'invoice_delay':
      return 'Send Reminder';
    case 'insurance_renewal':
    case 'permit_expiry':
      return 'Renew Now';
    case 'customer_profitability':
      return 'Renegotiate Rate';
    case 'emergency_cash':
      return 'Approve Advance';
    case 'duplicate_fuel':
      return 'Reject Bill';
    default:
      return 'Assign Action';
  }
}

/**
 * Premium Floating AI Opportunity Card designed for the scrolling deck.
 * Features glassmorphism, floating shadows, hover elevation, and interactive details.
 */
export function AiOpportunityCard({ opportunity, onAssign, onSchedule, onDismiss, onInvestigate, index = 0 }) {
  const [expanded, setExpanded] = useState(false);
  const o = opportunity;
  const sev = SEVERITY_CONFIG[o.severity] || SEVERITY_CONFIG.low;

  return (
    <div
      className={cn(
        'w-[350px] sm:w-[380px] md:w-[420px] flex-shrink-0 rounded-2xl transition-all duration-300 ease-out',
        'bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border border-border/40',
        'shadow-card hover:shadow-elevated hover:-translate-y-2',
        expanded ? 'ring-2 ring-brand-500/20 shadow-elevated bg-white dark:bg-slate-900' : ''
      )}
      style={{
        transform: expanded ? 'translateY(-8px)' : '',
      }}
    >
      <div className="p-5 flex flex-col h-full justify-between">
        <div>
          {/* Card Top: AI tag, Confidence, Severity */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-1.5 text-brand-600 dark:text-brand-400 text-[11px] font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI COPILOT</span>
            </div>
            
            <div className="flex items-center gap-2">
              <span className={cn(
                'text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider',
                sev.text, sev.bg
              )}>
                {sev.label}
              </span>
              <span className="text-[10px] text-content-muted">
                {o.confidence}% match
              </span>
            </div>
          </div>

          {/* Narrative Text */}
          <p className="text-[14px] text-content-secondary leading-relaxed tracking-wide font-normal mb-5 prose dark:prose-invert min-h-[75px]">
            {getConversationalNarrative(o)}
          </p>

          {/* Core Benefit Display */}
          <div className="bg-surface-secondary/50 border border-border/30 rounded-xl p-3 mb-4 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-content-muted uppercase tracking-wider block">Estimated Savings</span>
              <span className="text-lg font-bold text-content">₹{o.potentialSaving.toLocaleString('en-IN')}</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-content-muted uppercase tracking-wider block">ROI</span>
              <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">{o.expectedRoi}</span>
            </div>
          </div>

          {/* Inline toggled evidence */}
          {expanded && (
            <div className="space-y-4 pt-2 border-t border-border/30 animate-fade-in mb-4">
              <div>
                <span className="text-[10px] text-content-muted uppercase tracking-wider block mb-1">Telemetry Evidence</span>
                <ul className="space-y-1.5">
                  {o.evidence.slice(0, 2).map((ev, i) => (
                    <li key={i} className="text-xs text-content-secondary flex items-start gap-1.5 leading-relaxed">
                      <span className="w-1 h-1 rounded-full bg-content-muted mt-1.5 flex-shrink-0" />
                      <span>{ev}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-content-muted block">Resolution SLA</span>
                  <span className="font-semibold text-content">{o.eta}</span>
                </div>
                {(o.truck || o.driver) && (
                  <div>
                    <span className="text-content-muted block">Involved Asset</span>
                    <span className="font-semibold text-content truncate block">
                      {o.truck?.plate || o.driver?.name}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Action controls */}
        <div className="pt-3 border-t border-border/20 flex items-center justify-between mt-auto">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs font-medium text-content-secondary hover:text-content transition-colors"
          >
            {expanded ? 'Fewer details' : 'See evidence'}
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onDismiss?.(o.id)}
              className="p-1.5 rounded-lg text-content-muted hover:text-red-500 transition-colors"
              title="Dismiss"
            >
              <XCircle className="w-4 h-4" />
            </button>

            <button
              onClick={() => onAssign?.(o.id)}
              className="bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-3 py-1.5 rounded-lg transition-colors hover:shadow-green flex items-center gap-1 active:scale-[0.98]"
            >
              <span>{getPrimaryActionLabel(o.category)}</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return '';
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now - date;
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);

  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}
