import {
  CheckCircle2,
  Truck,
  TrendingUp,
  Clock,
  ChevronRight,
  Calendar,
  IndianRupee,
  Activity,
} from 'lucide-react';
import { cn } from '@/utils/cn';

/**
 * Sticky right sidebar showing quick stats, recent accepts, upcoming pickups, and activity.
 */
export function OpportunitySidebar({ opportunities = [], recentActivity = [] }) {
  const accepted = opportunities.filter((o) => o.status === 'accepted');
  const upcoming = opportunities
    .filter((o) => o.status === 'available' || o.status === 'accepted')
    .sort((a, b) => new Date(a.pickupDate) - new Date(b.pickupDate))
    .slice(0, 4);

  const totalRevenue = accepted.reduce((sum, o) => sum + o.revenue, 0);
  const avgDistance = opportunities.length
    ? Math.round(
        opportunities.reduce((sum, o) => sum + parseInt(o.distance), 0) / opportunities.length
      )
    : 0;

  return (
    <aside className="space-y-5">
      {/* Quick stats */}
      <SidebarCard title="Quick Statistics" icon={TrendingUp}>
        <div className="grid grid-cols-2 gap-3">
          <MiniStat label="Accepted Revenue" value={`₹${totalRevenue.toLocaleString('en-IN')}`} color="text-emerald-500" />
          <MiniStat label="Avg Distance" value={`${avgDistance} km`} color="text-blue-500" />
          <MiniStat label="Available" value={opportunities.filter((o) => o.status === 'available').length} color="text-violet-500" />
          <MiniStat label="Negotiating" value={opportunities.filter((o) => o.status === 'negotiating').length} color="text-amber-500" />
        </div>
      </SidebarCard>

      {/* Recent accepted */}
      <SidebarCard title="Recent Accepted" icon={CheckCircle2}>
        {accepted.length === 0 ? (
          <p className="text-xs text-content-muted italic">No accepted opportunities yet.</p>
        ) : (
          <div className="space-y-2.5">
            {accepted.slice(0, 4).map((o) => (
              <div
                key={o.id}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-secondary/80 transition-colors cursor-pointer group"
              >
                <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-content truncate">{o.customer}</p>
                  <p className="text-[10px] text-content-muted">{o.pickup} → {o.drop}</p>
                </div>
                <ChevronRight className="h-3 w-3 text-content-muted opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            ))}
          </div>
        )}
      </SidebarCard>

      {/* Upcoming pickups */}
      <SidebarCard title="Upcoming Pickups" icon={Calendar}>
        {upcoming.length === 0 ? (
          <p className="text-xs text-content-muted italic">No upcoming pickups.</p>
        ) : (
          <div className="space-y-2.5">
            {upcoming.map((o) => (
              <div
                key={o.id}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-secondary/80 transition-colors cursor-pointer group"
              >
                <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                  <Truck className="h-4 w-4 text-blue-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-content truncate">{o.customer}</p>
                  <p className="text-[10px] text-content-muted">
                    {new Date(o.pickupDate).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                    {' · '}
                    {o.pickup}
                  </p>
                </div>
                <span className={cn(
                  'text-[10px] font-medium px-1.5 py-0.5 rounded-md',
                  isToday(o.pickupDate)
                    ? 'bg-red-100 text-red-600'
                    : 'bg-surface-secondary text-content-muted'
                )}>
                  {isToday(o.pickupDate) ? 'Today' : isTomorrow(o.pickupDate) ? 'Tomorrow' : formatDate(o.pickupDate)}
                </span>
              </div>
            ))}
          </div>
        )}
      </SidebarCard>

      {/* Recent activity */}
      <SidebarCard title="Recent Activity" icon={Activity}>
        {recentActivity.length === 0 ? (
          <p className="text-xs text-content-muted italic">No recent activity.</p>
        ) : (
          <div className="space-y-2.5">
            {recentActivity.map((act) => (
              <div key={act.id} className="flex items-start gap-2.5 py-1">
                <div className={cn(
                  'w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0',
                  act.action === 'Accepted' ? 'bg-emerald-500'
                    : act.action === 'Rejected' ? 'bg-red-500'
                      : 'bg-amber-500'
                )} />
                <div className="min-w-0">
                  <p className="text-xs text-content">
                    <span className="font-medium">{act.action}</span>
                    {' '}
                    <span className="text-content-muted">{act.opportunity}</span>
                  </p>
                  <p className="text-[10px] text-content-muted mt-0.5">
                    {act.customer} · {act.time}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </SidebarCard>
    </aside>
  );
}

function SidebarCard({ title, icon: Icon, children }) {
  return (
    <div className="bg-surface border border-border rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="h-4 w-4 text-content-muted" strokeWidth={1.8} />
        <h3 className="text-xs font-semibold text-content-muted uppercase tracking-wider">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function MiniStat({ label, value, color }) {
  return (
    <div className="p-2.5 rounded-xl bg-surface-secondary/60">
      <p className={cn('text-base font-bold', color)}>{value}</p>
      <p className="text-[10px] text-content-muted mt-0.5">{label}</p>
    </div>
  );
}

function isToday(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}

function isTomorrow(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  now.setDate(now.getDate() + 1);
  return d.toDateString() === now.toDateString();
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}
