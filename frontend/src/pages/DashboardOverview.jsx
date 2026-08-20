import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  RefreshCw, Bell, Search, Mic, Send, Globe, User,
  Truck, Package, CheckCircle2, Wrench, Route, Fuel,
  CreditCard, AlertTriangle, ShieldAlert, ChevronRight,
  ArrowRight, ChevronDown, ChevronUp, Sparkles, Clock, XCircle,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/utils/cn';
import { useLanguage } from '@/i18n/LanguageContext';
import { LanguageSelector } from '@/components/shared/LanguageSelector';
import { NotificationBell } from '@/components/shared/NotificationDropdown';
import { getInitials } from '@/utils/formatters';
import {
  fetchAiOpportunities,
  assignOpportunity,
  dismissOpportunity,
  scheduleOpportunity,
} from '@/services/aiOpportunities';
import { getFleetHealth, getUpcomingAlerts, getRecentActions } from '@/api/dashboardApi';
import {
  MOCK_KPIS,
  MOCK_FLEET_STATUS,
  MOCK_FLEET_HEALTH,
  MOCK_RECENT_ACTIVITY,
  MOCK_FLEET_SUMMARY,
  MOCK_ALERTS,
  MOCK_PREDICTIVE_SIGNAL,
} from '@/data/dashboardMockData';
import { Modal } from '@/components/ui/Modal';
import { ConfidenceRing } from './dashboard-ai/ConfidenceRing';
import { AiCopilot } from './dashboard-ai/AiCopilot';
import { SignalDeck } from './dashboard-ai/SignalDeck';
import { FleetMap } from './dashboard-ai/FleetMap';
import { FinancialIntelligenceWidget } from '@/components/dashboard/FinancialIntelligenceWidget';
// ── KPI Icon Map ──
const kpiIcons = {
  Truck: Truck,
  Package: Package,
  CheckCircle2: CheckCircle2,
  Wrench: Wrench,
};

// ── Activity Icon Map ──
const activityIcons = {
  Route: Route,
  Fuel: Fuel,
  Package: Package,
  CreditCard: CreditCard,
};

// ── Mini Tooltip for charts ──
function MiniTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-border px-2.5 py-1.5 rounded-lg text-xs font-medium text-content shadow-elevated">
      ₹{payload[0].value?.toLocaleString('en-IN')}
    </div>
  );
}

export default function DashboardOverview() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { success, error, info } = useToast();
  
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [health, setHealth] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [signalExpanded, setSignalExpanded] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [selectedAction, setSelectedAction] = useState('tech');
  const [resolving, setResolving] = useState(false);

  useEffect(() => {
    const cached = localStorage.getItem('fleetguard_user') || sessionStorage.getItem('fleetguard_user');
    if (cached) setUser(JSON.parse(cached));
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return 'Good morning';
    if (hour >= 12 && hour < 16) return 'Good afternoon';
    return 'Good evening';
  };

  const loadData = async (isSilent = false) => {
    if (isSilent) setRefreshing(true);
    else setLoading(true);
    try {
      const [res, healthData, alertsData] = await Promise.all([
        fetchAiOpportunities().catch(() => ({ data: [] })),
        getFleetHealth().catch(() => ({})),
        getUpcomingAlerts().catch(() => []),
      ]);
      setOpportunities(res?.data || []);
      setHealth(healthData || {});
      setAlerts(alertsData || []);
    } catch {
      // Use mock data on error — no disruption
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleAssign = async (id) => {
    setResolveModalOpen(true);
  };

  const handleConfirmResolve = async (id) => {
    setResolving(true);
    try {
      await assignOpportunity(id);
      success('Signal Resolved', `Executed protocol '${selectedAction}' for signal ${id}`);
      setOpportunities(prev => prev.map(o => o.id === id ? { ...o, status: 'assigned' } : o));
      setResolveModalOpen(false);
    } catch {
      error('Resolution Failed', 'Could not execute the assignment.');
    } finally {
      setResolving(false);
    }
  };

  const handleDismiss = async (id) => {
    try {
      await dismissOpportunity(id);
      info('Signal Dismissed', `${id} archived successfully.`);
      setOpportunities(prev => prev.filter(o => o.id !== id));
    } catch {
      error('Action Failed', 'Could not archive the signal.');
    }
  };

  const handleSearchSubmit = () => {
    if (searchValue.trim()) {
      navigate('/dashboard/chatbox', { state: { initialMessage: searchValue } });
    } else {
      navigate('/dashboard/chatbox');
    }
  };

  const activeOpportunities = (opportunities || []).filter(o => o && (o.status === 'new' || o.status === 'investigating'));
  const totalSavings = activeOpportunities.reduce((sum, o) => sum + (o?.potentialSaving || 0), 0);
  const displaySignal = activeOpportunities[0] || MOCK_PREDICTIVE_SIGNAL;
  const displayAlerts = alerts.length > 0 ? alerts.map(a => ({
    id: a.id,
    icon: a.severity === 'critical' ? 'ShieldAlert' : 'AlertTriangle',
    text: a.text,
    detail: '',
    severity: a.severity,
  })) : MOCK_ALERTS;

  const userName = user?.name || 'Dev1';
  const signalCount = activeOpportunities.length || 1;
  const savingsAmount = totalSavings || 475;

  return (
    <div className="flex w-full min-h-full bg-surface-base overflow-x-hidden">
      
      {/* ── MAIN WORKSPACE (LEFT) ── */}
      <div className="flex-1 overflow-y-auto px-5 lg:px-8 py-6 space-y-6 fg-scrollbar animate-fade-in pb-24">
        
        {/* ═══════════ HEADER & AI COMMAND BAR ═══════════ */}
        <div className="space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-light text-content tracking-tight">
                {t(getGreeting())}, <span className="font-semibold">{userName}</span> 👋
              </h1>
              <p className="mt-1.5 text-sm text-content-secondary flex items-center gap-2">
                {((alerts || []).length > 0 || (opportunities || []).filter(o => o?.status === 'new' || o?.status === 'investigating').length > 0) ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    {t("You have")} {
                      [
                        (alerts || []).length > 0 ? `${(alerts || []).length} ${t("alerts")}` : null,
                        (opportunities || []).filter(o => o?.status === 'new' || o?.status === 'investigating').length > 0 ? `${(opportunities || []).filter(o => o?.status === 'new' || o?.status === 'investigating').length} ${t("opportunities")}` : null
                      ].filter(Boolean).join(` ${t("and")} `)
                    } {t("needing attention.")}
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-brand-500" />
                    {t("All systems are running smoothly.")}
                  </>
                )}
              </p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={() => loadData(true)}
                className="p-2 rounded-xl border border-border bg-surface hover:bg-surface-secondary text-content-secondary transition-colors shadow-sm"
                title={t("Refresh")}
              >
                <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              </button>
            </div>
          </div>

          <div className="relative group w-full max-w-5xl">
            <div className="flex items-center gap-3 bg-white border border-border rounded-2xl px-5 py-3.5 
            hover:border-brand-300 focus-within:border-brand-400 focus-within:shadow-[0_0_20px_rgba(34,197,94,0.10)] transition-all duration-300">
            <Search className="w-5 h-5 text-content-muted flex-shrink-0" />
            <input
              type="text"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
              placeholder={`Ask something, ${userName}...`}
              className="flex-1 bg-transparent border-none outline-none text-sm text-content placeholder:text-content-muted font-light"
            />
            <button className="p-1.5 rounded-lg hover:bg-surface-secondary text-content-secondary transition-colors">
              <Mic className="w-4 h-4" />
            </button>
            <button
              onClick={handleSearchSubmit}
              className="p-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white transition-colors shadow-sm"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
        </div>

        {/* ═══════════ KPI ROW (COMPACT) ═══════════ */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          {MOCK_KPIS.map((kpi, i) => {
            const Icon = kpiIcons[kpi.icon] || Truck;
            return (
              <motion.div
                key={kpi.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06, duration: 0.4 }}
                className="group relative overflow-hidden bg-white border border-border rounded-2xl p-4 transition-all hover:shadow-elevated hover:border-brand-200 cursor-default"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-brand-50/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                
                <div className="flex items-start justify-between relative z-10">
                  <div className="space-y-1">
                    <p className="text-[10px] text-content-secondary uppercase tracking-widest font-semibold">{t(kpi.label)}</p>
                    <p className="text-2xl font-bold text-content tracking-tight">{kpi.value}</p>
                  </div>
                  <div className="p-2 rounded-xl bg-surface-tertiary border border-border/50 group-hover:scale-110 transition-transform">
                    <Icon className="w-4 h-4" style={{ color: kpi.color }} strokeWidth={2} />
                  </div>
                </div>
                
                {/* Tiny pseudo trend line */}
                <div className="mt-3 flex items-center gap-1.5 relative z-10">
                  <div className="w-1 h-1 rounded-full" style={{ backgroundColor: kpi.color }} />
                  <p className="text-[10px] text-content-muted">{kpi.trend}</p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* ═══════════ FLEET FINANCIAL INTELLIGENCE ═══════════ */}
        <div className="mt-6">
          <FinancialIntelligenceWidget />
        </div>

        {/* ═══════════ OPERATIONS WORKSPACE (DECK & MAP) ═══════════ */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-6">
          {/* ── Signal Deck (Left) ── */}
          <div className="lg:col-span-5 h-[540px]">
            <SignalDeck signals={activeOpportunities.length > 0 ? activeOpportunities : [MOCK_PREDICTIVE_SIGNAL]} onResolve={handleAssign} />
          </div>

          {/* ── Fleet Map (Right) ── */}
          <div className="lg:col-span-7 h-[540px]">
             <FleetMap trucks={[
               { id: 'KA-01-HH-1234', lat: 12.9716, lng: 77.5946, status: 'active', speed: '45 km/h' },
               { id: 'MH-12-AB-9876', lat: 12.9352, lng: 77.6245, status: 'idle', speed: '0 km/h' },
               { id: 'DL-01-XX-1111', lat: 13.0012, lng: 77.5566, status: 'active', speed: '62 km/h' }
             ]} />
          </div>
        </div>

        {/* ═══════════ BOTTOM SECTION ═══════════ */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* ── Recent Activity ── */}
          <div className="bg-white border border-border rounded-2xl p-5 shadow-card">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest">{t("Recent Activity")}</h4>
              <button className="text-[10px] text-brand-500 hover:text-brand-600 transition-colors font-medium">{t("VIEW ALL")}</button>
            </div>
            <div className="space-y-3">
              {MOCK_RECENT_ACTIVITY.map((item) => {
                const Icon = activityIcons[item.icon] || Route;
                return (
                  <div key={item.id} className="flex items-start gap-3 py-1.5 group cursor-default">
                    <div className="mt-0.5 p-1.5 rounded-lg bg-surface-tertiary border border-border group-hover:border-brand-300 transition-colors">
                      <Icon className="w-3.5 h-3.5" style={{ color: item.color }} strokeWidth={1.5} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] text-content font-light leading-snug">{item.text}</p>
                      <p className="text-[11px] text-content-muted mt-0.5">{item.time}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Fleet Summary ── */}
          <div className="bg-surface/40 backdrop-blur-md border border-border rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest">{t("Fleet Summary")}</h4>
              <span className="text-[10px] text-content-secondary bg-surface-secondary border border-border px-2 py-0.5 rounded-lg">{t("This Week")}</span>
            </div>
            <div className="space-y-2 mb-4">
              {[
                { label: 'Total Distance', value: MOCK_FLEET_SUMMARY.totalDistance },
                { label: 'Fuel Consumed', value: MOCK_FLEET_SUMMARY.fuelConsumed },
                { label: 'Avg. Fuel Efficiency', value: MOCK_FLEET_SUMMARY.avgFuelEfficiency },
                { label: 'Total Earnings', value: MOCK_FLEET_SUMMARY.totalEarnings, highlight: true },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between py-1">
                  <span className="text-[13px] text-content-secondary font-light">{t(item.label)}</span>
                  <span className={cn('text-[13px] font-semibold tabular-nums', item.highlight ? 'text-brand-500' : 'text-content')}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
            {/* Trend Chart */}
            <div className="pt-2 border-t border-border">
              <h5 className="text-[10px] text-content-muted font-semibold tracking-widest uppercase mb-2">
                Daily Earnings Trend
              </h5>
              <div className="h-32 -mx-2">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={MOCK_FLEET_SUMMARY.chartData} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="fleetSummaryGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#22C55E" stopOpacity={0.15} />
                        <stop offset="100%" stopColor="#22C55E" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="day" 
                      stroke="#94a3b8" 
                      fontSize={9} 
                      tickLine={false} 
                      axisLine={false}
                      dy={5}
                    />
                    <YAxis 
                      hide={false}
                      stroke="#94a3b8" 
                      fontSize={9} 
                      tickLine={false} 
                      axisLine={false}
                      width={30}
                      tickFormatter={(val) => `₹${val / 1000}k`}
                      domain={['dataMin - 200', 'dataMax + 200']} 
                    />
                    <Tooltip content={<MiniTooltip />} cursor={{ stroke: 'rgba(34,197,94,0.15)', strokeWidth: 1 }} />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#22C55E"
                      strokeWidth={2}
                      fill="url(#fleetSummaryGrad)"
                      dot={{ r: 2, fill: '#22C55E', stroke: '#22C55E' }}
                      activeDot={{ r: 4, stroke: '#22C55E', strokeWidth: 1.5, fill: '#FFFFFF' }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* ── Alerts ── */}
          <div className="bg-surface/40 backdrop-blur-md border border-border rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest">{t("Alerts")}</h4>
              <button
                onClick={() => navigate('/dashboard/alerts')}
                className="text-[10px] text-brand-500 hover:text-brand-600 transition-colors font-medium"
              >
                {t("VIEW ALL")}
              </button>
            </div>
            <div className="space-y-3">
              {displayAlerts.slice(0, 3).map((alert, i) => (
                <div key={alert.id || i} className="flex items-start gap-3 py-1.5 cursor-pointer group">
                  <div className={cn(
                    'mt-0.5 p-1.5 rounded-lg border transition-colors',
                    alert.severity === 'critical'
                      ? 'bg-red-500/10 border-red-500/20 group-hover:border-red-500/40'
                      : 'bg-amber-500/10 border-amber-500/20 group-hover:border-amber-500/40'
                  )}>
                    {alert.severity === 'critical'
                      ? <ShieldAlert className="w-3.5 h-3.5 text-red-400" strokeWidth={1.5} />
                      : <AlertTriangle className="w-3.5 h-3.5 text-amber-400" strokeWidth={1.5} />
                    }
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] text-content font-light leading-snug">{alert.text}</p>
                    {alert.detail && (
                      <p className="text-[11px] text-content-muted mt-0.5">{alert.detail}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── AI CO-PILOT (FLOATING WIDGET) ── */}
      <AiCopilot />

      {/* ═══════════ SIGNAL RESOLUTION MODAL ═══════════ */}
      <Modal
        open={resolveModalOpen}
        onClose={() => setResolveModalOpen(false)}
        size="lg"
        title="Operations Engine — Resolve Signal"
        description="Select a resolution protocol to execute for this predictive signal."
      >
        <div className="space-y-5 text-content">
          {/* Signal summary card */}
          <div className="p-4 rounded-xl bg-surface-secondary border border-border space-y-2">
            <div className="flex items-center justify-between text-xs text-content-secondary">
              <span className="font-semibold text-brand-500 uppercase tracking-wider">{displaySignal.category?.replace('_', ' ') || 'Fuel Waste'}</span>
              <span className="text-amber-400 font-semibold uppercase">{displaySignal.severity || 'Medium'} Priority</span>
            </div>
            <h4 className="text-base font-medium text-content">{displaySignal.title}</h4>
            <div className="flex items-center gap-6 text-xs text-content-secondary pt-1">
              <span>Vehicle: <strong className="text-content font-semibold">{displaySignal.truck?.plate || 'KA-01-HH-1234'}</strong></span>
              <span>Monthly Savings: <strong className="text-brand-500 font-semibold">₹{(displaySignal.savings || displaySignal.potentialSaving || 475).toLocaleString('en-IN')}</strong></span>
              <span>Confidence: <strong className="text-content font-semibold">{displaySignal.confidence || 90}%</strong></span>
            </div>
          </div>

          {/* Protocol Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-content-secondary uppercase tracking-widest block">Select Action Protocol</label>
            {[
              { id: 'tech', label: 'Dispatch Field Technician for Tank & Sensor Inspection', desc: 'Schedules on-site telemetry sensor diagnostic at nearest yard within 24 hours.' },
              { id: 'calibrate', label: 'Recalibrate GPS & Telematics Fuel Flow Meter', desc: 'Triggers remote OTA recalibration signal to vehicle gateway.' },
              { id: 'audit', label: 'Flag Driver for Fueling Discrepancy Verification', desc: 'Sends automated WhatsApp confirmation request to driver for recent receipts.' },
            ].map((proto) => (
              <div
                key={proto.id}
                onClick={() => setSelectedAction(proto.id)}
                className={cn(
                  'p-3.5 rounded-xl border cursor-pointer transition-all duration-200 flex items-start gap-3',
                  selectedAction === proto.id
                    ? 'bg-brand-50 border-brand-400 shadow-[0_0_15px_rgba(34,197,94,0.10)]'
                    : 'bg-white border-border hover:bg-surface-tertiary'
                )}
              >
                <input
                  type="radio"
                  name="resolution-proto"
                  checked={selectedAction === proto.id}
                  onChange={() => setSelectedAction(proto.id)}
                  className="mt-1 accent-[#19B86A]"
                />
                <div>
                  <p className="text-sm font-medium text-content">{proto.label}</p>
                  <p className="text-xs text-content-secondary mt-0.5 font-light">{proto.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Footer buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
            <button
              onClick={() => setResolveModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-medium text-content-secondary hover:text-content hover:bg-surface-secondary transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => handleConfirmResolve(displaySignal.id)}
              disabled={resolving}
              className="px-5 py-2 rounded-xl text-xs font-semibold bg-brand-500 hover:bg-brand-600 text-white transition-all shadow-green"
            >
              {resolving ? 'Executing Protocol...' : 'Confirm & Execute Resolution'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
