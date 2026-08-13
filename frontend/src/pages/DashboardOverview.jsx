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
import { Fleet3DScene } from './dashboard-ai/Fleet3DScene';

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
    <div className="bg-fg-deep border border-fg-border px-2.5 py-1.5 rounded-lg text-xs font-medium text-fg-text shadow-lg">
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
    <div className="max-w-[1440px] mx-auto space-y-6 animate-fade-in">

      {/* ═══════════ HEADER ═══════════ */}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-light text-fg-text tracking-tight">
            {t(getGreeting())}, <span className="font-semibold">{userName}</span> 👋
          </h1>
          <p className="text-sm text-fg-text-sec mt-1">
            {t("Operations Engine identified")} <span className="text-fg-text font-medium">{signalCount} {t("signals")}</span>{' '}
            {t("saving up to")} <span className="text-fg-text font-medium">₹{savingsAmount.toLocaleString('en-IN')}</span> {t("this month.")}
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

      {/* ═══════════ AI SEARCH BAR ═══════════ */}
      <div className="relative group">
        <div className="flex items-center gap-3 bg-fg-card border border-fg-border rounded-2xl px-5 py-3.5 
          hover:border-fg-green/20 focus-within:border-fg-green/30 focus-within:shadow-fg-glow transition-all duration-300">
          <Search className="w-5 h-5 text-fg-text-sec flex-shrink-0" />
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
            placeholder={`Ask something, ${userName}...`}
            className="flex-1 bg-transparent border-none outline-none text-sm text-fg-text placeholder:text-fg-text-sec/50 font-light"
          />
          <button className="p-1.5 rounded-lg hover:bg-white/[0.05] text-fg-text-sec transition-colors">
            <Mic className="w-4 h-4" />
          </button>
          <button
            onClick={handleSearchSubmit}
            className="p-2 rounded-xl bg-fg-green hover:bg-fg-green-bright text-fg-dark transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ═══════════ OPERATIONS ENGINE (HERO 3D) ═══════════ */}
      <div className="relative w-full h-[480px] lg:h-[400px] rounded-3xl overflow-hidden border border-border shadow-md bg-fg-deep/40 mt-2 flex flex-col lg:flex-row">
        {/* Background 3D Scene */}
        <div className="absolute inset-0 z-0">
          <Fleet3DScene />
        </div>
        
        {/* Subtle glass gradient overlay for text legibility */}
        <div className="absolute inset-0 z-0 bg-gradient-to-r from-surface via-surface/80 to-transparent pointer-events-none" />

        {/* Foreground Content - Left Side */}
        <div className="relative z-10 w-full lg:w-1/2 p-6 lg:p-10 flex flex-col justify-center">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-[10px] font-bold text-fg-green uppercase tracking-[0.2em] flex items-center gap-2 mb-1">
                <Sparkles className="w-3.5 h-3.5" />
                {t("Operations Engine")}
              </h2>
              <p className="text-xs text-content-secondary">{t("Real-time predictive telemetry")}</p>
            </div>
            <button
              onClick={() => loadData(true)}
              className="p-1.5 rounded-lg bg-surface-secondary/50 hover:bg-surface-secondary text-content-secondary transition-colors border border-border backdrop-blur-md"
            >
              <RefreshCw className={cn("w-3.5 h-3.5", refreshing && "animate-spin")} />
            </button>
          </div>

          <div className="bg-surface/50 backdrop-blur-xl border border-border/60 rounded-2xl p-5 shadow-lg relative overflow-hidden">
            {/* Edge highlight line */}
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-fg-green to-transparent" />
            
            <div className="flex items-center gap-3 text-[11px] text-content-secondary mb-3">
              <span className="font-semibold text-fg-green tracking-wider uppercase">{t("Signal")}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
              <span className="font-semibold uppercase tracking-wider text-amber-400">{t("Medium Priority")}</span>
              <span className="flex items-center gap-1 ml-auto">
                <Clock className="w-3.5 h-3.5" />
                {displaySignal.time || '06:44 am'}
              </span>
            </div>

            <h3 className="text-lg lg:text-xl font-light text-content tracking-tight leading-snug mb-3">
              {displaySignal.title}
            </h3>

            <p className="text-sm text-content-muted leading-relaxed font-light mb-5">
              {displaySignal.narrative || `Fuel efficiency dropped significantly on truck ${displaySignal.truck?.plate}. Average fuel economy fell from 4.8 km/L to 3.9 km/L over the last 26 days. This drop is costing you roughly ₹${displaySignal.savings || displaySignal.potentialSaving || 475} per month.`}
            </p>

            <div className="flex items-center gap-8 flex-wrap">
              <div>
                <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Monthly Savings")}</span>
                <p className="text-xl font-bold text-content">
                  ₹{(displaySignal.savings || displaySignal.potentialSaving || 475).toLocaleString('en-IN')}
                </p>
              </div>
              <div>
                <span className="text-[10px] text-content-muted uppercase tracking-widest block mb-1">{t("Confidence")}</span>
                <ConfidenceRing percentage={displaySignal.confidence || 90} size={42} strokeWidth={2.5} />
              </div>
            </div>

            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setResolveModalOpen(true)}
                className="flex-1 bg-fg-green hover:bg-fg-green-bright text-fg-dark py-2.5 rounded-xl font-semibold text-sm transition-all shadow-[0_0_15px_rgba(25,184,106,0.3)] hover:shadow-[0_0_25px_rgba(25,184,106,0.5)] active:scale-[0.98]"
              >
                {t("Resolve Signal")}
              </button>
              <button
                onClick={() => setRightPanelOpen(!rightPanelOpen)}
                className="flex-1 bg-surface-secondary hover:bg-surface border border-border text-content py-2.5 rounded-xl font-medium text-sm transition-all active:scale-[0.98]"
              >
                {t("View Telemetry")} →
              </button>
            </div>
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
              className="group relative overflow-hidden bg-surface/40 backdrop-blur-md border border-border rounded-2xl p-4 transition-all hover:shadow-fg-glow hover:bg-surface-secondary/80 cursor-default"
            >
              {/* Subtle hover gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              
              <div className="flex items-start justify-between relative z-10">
                <div className="space-y-1">
                  <p className="text-[10px] text-content-secondary uppercase tracking-widest font-semibold">{t(kpi.label)}</p>
                  <p className="text-2xl font-bold text-content tracking-tight">{kpi.value}</p>
                </div>
                <div className="p-2 rounded-xl bg-surface border border-border/50 group-hover:scale-110 transition-transform">
                  <Icon className="w-4 h-4" style={{ color: kpi.color }} strokeWidth={2} />
                </div>
              </div>
              
              {/* Tiny pseudo trend line */}
              <div className="mt-3 flex items-center gap-1.5 relative z-10">
                <div className="w-1 h-1 rounded-full bg-fg-green" />
                <p className="text-[10px] text-content-muted">+2.4% from last week</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* ═══════════ MAIN CONTENT GRID ═══════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-6">

        {/* ── LEFT: Main Feed (8 cols) ── */}
        <div className="lg:col-span-8 space-y-5">

            {/* Activity Feed Placeholder */}
            <div className="relative z-10 bg-surface/40 backdrop-blur-md border border-border rounded-2xl p-5 space-y-4 shadow-sm">
              <h3 className="text-lg font-light text-content tracking-tight leading-snug">
                {t("Today's Operations")}
              </h3>
              <p className="text-sm text-content-muted">
                {t("Operations engine is actively monitoring fleet telemetry.")}
              </p>
            </div>
          </div>

        {/* ── RIGHT: Data Rail (4 cols) ── */}
        <div className="lg:col-span-4 space-y-4">
          {/* Fleet Status */}
          <div className="fg-card-static p-5">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-[10px] font-semibold text-fg-text-sec uppercase tracking-widest">{t("Fleet Status")}</h4>
              <button className="text-[10px] text-fg-green hover:text-fg-green-bright transition-colors font-medium">{t("VIEW ALL")}</button>
            </div>
            <div className="space-y-0.5">
              {MOCK_FLEET_STATUS.map((item, i) => (
                <div key={i} className="flex items-center justify-between py-2 px-2 rounded-lg hover:bg-white/[0.03] transition-colors">
                  <span className="text-[13px] text-fg-text-sec font-light">{t(item.label)}</span>
                  <div className="flex items-center gap-2">
                    {item.progress != null && (
                      <div className="w-14 fg-progress-track">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${item.progress}%` }}
                          viewport={{ once: true }}
                          transition={{ delay: 0.2 + i * 0.05, duration: 0.6 }}
                          className="fg-progress-fill"
                        />
                      </div>
                    )}
                    <span className="text-[13px] font-semibold text-fg-text tabular-nums">{item.value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Fleet Health */}
          <div className="fg-card-static p-5">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-[10px] font-semibold text-fg-text-sec uppercase tracking-widest">{t("Fleet Health")}</h4>
              <button className="text-[10px] text-fg-green hover:text-fg-green-bright transition-colors font-medium">{t("VIEW ALL")}</button>
            </div>
            <div className="space-y-0.5">
              {MOCK_FLEET_HEALTH.map((item, i) => (
                <div key={i} className="flex items-center justify-between py-2 px-2 rounded-lg hover:bg-white/[0.03] transition-colors">
                  <span className="text-[13px] text-fg-text-sec font-light">{t(item.label)}</span>
                  <span className={cn(
                    'text-[13px] font-semibold tabular-nums',
                    item.status === 'good' ? 'text-fg-green' :
                    item.status === 'warning' ? 'text-amber-400' :
                    'text-fg-text'
                  )}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════ BOTTOM SECTION — 3 Cards ═══════════ */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

        {/* ── Recent Activity ── */}
        <div className="fg-card-static p-5">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-[10px] font-semibold text-fg-text-sec uppercase tracking-widest">{t("Recent Activity")}</h4>
            <button className="text-[10px] text-fg-green hover:text-fg-green-bright transition-colors font-medium">{t("VIEW ALL")}</button>
          </div>
          <div className="space-y-3">
            {MOCK_RECENT_ACTIVITY.map((item) => {
              const Icon = activityIcons[item.icon] || Route;
              return (
                <div key={item.id} className="flex items-start gap-3 py-1.5 group cursor-default">
                  <div className="mt-0.5 p-1.5 rounded-lg bg-white/[0.03] border border-fg-border group-hover:border-fg-green/20 transition-colors">
                    <Icon className="w-3.5 h-3.5" style={{ color: item.color }} strokeWidth={1.5} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] text-fg-text font-light leading-snug">{item.text}</p>
                    <p className="text-[11px] text-fg-text-sec/60 mt-0.5">{item.time}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Fleet Summary ── */}
        <div className="fg-card-static p-5">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-[10px] font-semibold text-fg-text-sec uppercase tracking-widest">{t("Fleet Summary")}</h4>
            <span className="text-[10px] text-fg-text-sec bg-white/[0.03] border border-fg-border px-2 py-0.5 rounded-lg">{t("This Week")}</span>
          </div>
          <div className="space-y-2 mb-4">
            {[
              { label: 'Total Distance', value: MOCK_FLEET_SUMMARY.totalDistance },
              { label: 'Fuel Consumed', value: MOCK_FLEET_SUMMARY.fuelConsumed },
              { label: 'Avg. Fuel Efficiency', value: MOCK_FLEET_SUMMARY.avgFuelEfficiency },
              { label: 'Total Earnings', value: MOCK_FLEET_SUMMARY.totalEarnings, highlight: true },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between py-1">
                <span className="text-[13px] text-fg-text-sec font-light">{t(item.label)}</span>
                <span className={cn('text-[13px] font-semibold tabular-nums', item.highlight ? 'text-fg-green' : 'text-fg-text')}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>
          {/* Mini Area Chart */}
          <div className="h-16 -mx-2 -mb-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={MOCK_FLEET_SUMMARY.chartData} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
                <defs>
                  <linearGradient id="fleetSummaryGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#19B86A" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="#19B86A" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" hide />
                <YAxis hide domain={['dataMin - 200', 'dataMax + 200']} />
                <Tooltip content={<MiniTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.05)', strokeWidth: 1 }} />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#19B86A"
                  strokeWidth={1.5}
                  fill="url(#fleetSummaryGrad)"
                  dot={false}
                  activeDot={{ r: 3, stroke: '#19B86A', strokeWidth: 1.5, fill: '#050B09' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* ── Alerts ── */}
        <div className="fg-card-static p-5">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-[10px] font-semibold text-fg-text-sec uppercase tracking-widest">{t("Alerts")}</h4>
            <button
              onClick={() => navigate('/dashboard/alerts')}
              className="text-[10px] text-fg-green hover:text-fg-green-bright transition-colors font-medium"
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
                  <p className="text-[13px] text-fg-text font-light leading-snug">{alert.text}</p>
                  {alert.detail && (
                    <p className="text-[11px] text-fg-text-sec/60 mt-0.5">{alert.detail}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      {/* ═══════════ SIGNAL RESOLUTION MODAL ═══════════ */}
      <Modal
        open={resolveModalOpen}
        onClose={() => setResolveModalOpen(false)}
        size="lg"
        title="Operations Engine — Resolve Signal"
        description="Select a resolution protocol to execute for this predictive signal."
      >
        <div className="space-y-5 text-fg-text">
          {/* Signal summary card */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-fg-border space-y-2">
            <div className="flex items-center justify-between text-xs text-fg-text-sec">
              <span className="font-semibold text-fg-green uppercase tracking-wider">{displaySignal.category?.replace('_', ' ') || 'Fuel Waste'}</span>
              <span className="text-amber-400 font-semibold uppercase">{displaySignal.severity || 'Medium'} Priority</span>
            </div>
            <h4 className="text-base font-medium text-fg-text">{displaySignal.title}</h4>
            <div className="flex items-center gap-6 text-xs text-fg-text-sec pt-1">
              <span>Vehicle: <strong className="text-fg-text font-semibold">{displaySignal.truck?.plate || 'KA-01-HH-1234'}</strong></span>
              <span>Monthly Savings: <strong className="text-fg-green font-semibold">₹{(displaySignal.savings || displaySignal.potentialSaving || 475).toLocaleString('en-IN')}</strong></span>
              <span>Confidence: <strong className="text-fg-text font-semibold">{displaySignal.confidence || 90}%</strong></span>
            </div>
          </div>

          {/* Protocol Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-fg-text-sec uppercase tracking-widest block">Select Action Protocol</label>
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
                    ? 'bg-fg-green-deep/30 border-fg-green shadow-fg-glow'
                    : 'bg-white/[0.02] border-fg-border hover:bg-white/[0.04]'
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
                  <p className="text-sm font-medium text-fg-text">{proto.label}</p>
                  <p className="text-xs text-fg-text-sec mt-0.5 font-light">{proto.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Footer buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-fg-border">
            <button
              onClick={() => setResolveModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-medium text-fg-text-sec hover:text-fg-text hover:bg-white/[0.05] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => handleConfirmResolve(displaySignal.id)}
              disabled={resolving}
              className="px-5 py-2 rounded-xl text-xs font-semibold bg-fg-green hover:bg-fg-green-bright text-fg-dark transition-all shadow-fg-glow"
            >
              {resolving ? 'Executing Protocol...' : 'Confirm & Execute Resolution'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
