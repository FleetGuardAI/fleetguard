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
import { getDashboardData, getFleetHealth, getUpcomingAlerts } from '@/api/dashboardApi';
import { getLiveTracking } from '@/api/telematicsApi';
import { FleetMap } from './dashboard-ai/FleetMap';
import { OperationsEngine } from '@/components/dashboard/OperationsEngine';
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
  const [searchValue, setSearchValue] = useState('');

  // Real data state
  const [dashboardData, setDashboardData] = useState({
    kpis: { active_trucks: 0, pending_approvals: 0, theft_alerts: 0, flagged_drivers: 0, total_expenses_today: 0, total_expenses_month: 0 },
    recentActivity: [],
    fuelChart: []
  });
  const [liveTrucks, setLiveTrucks] = useState([]);

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
      const [healthData, alertsData, dbData, tracking] = await Promise.all([
        getFleetHealth().catch(() => ({})),
        getUpcomingAlerts().catch(() => []),
        getDashboardData().catch(() => ({ kpis: {}, recentActivity: [], fuelChart: [] })),
        getLiveTracking().catch(() => [])
      ]);
      setHealth(healthData || {});
      setAlerts(alertsData || []);
      setDashboardData({
        kpis: dbData.kpis || {},
        recentActivity: dbData.recentActivity || [],
        fuelChart: dbData.fuelChart || []
      });
      setLiveTrucks(tracking || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { loadData(); }, []);



  const handleSearchSubmit = () => {
    if (searchValue.trim()) {
      navigate('/dashboard/chatbox', { state: { initialMessage: searchValue } });
    } else {
      navigate('/dashboard/chatbox');
    }
  };

  const userName = user?.name || 'Owner';

  const kpiItems = [
    { id: 'trucks', label: 'Active Trucks', value: dashboardData.kpis.active_trucks || 0, icon: 'Truck', trend: 'Online now', color: '#3B82F6' },
    { id: 'approvals', label: 'Pending Approvals', value: dashboardData.kpis.pending_approvals || 0, icon: 'CheckCircle2', trend: 'Needs review', color: '#EAB308' },
    { id: 'theft', label: 'Theft Alerts', value: dashboardData.kpis.theft_alerts || 0, icon: 'ShieldAlert', trend: 'Last 24h', color: '#EF4444' },
    { id: 'expenses', label: 'Monthly Expenses', value: `₹${(dashboardData.kpis.total_expenses_month || 0).toLocaleString('en-IN')}`, icon: 'CreditCard', trend: 'This month', color: '#22C55E' },
  ];

  return (
    <div className="flex w-full min-h-full bg-surface-base overflow-x-hidden">
      <div className="flex-1 overflow-y-auto px-5 lg:px-8 py-6 space-y-6 fg-scrollbar animate-fade-in pb-24">
        
        {/* Header */}
        <div className="space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-light text-content tracking-tight">
                {t(getGreeting())}, <span className="font-semibold">{userName}</span> 👋
              </h1>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button onClick={() => loadData(true)} className="p-2 rounded-xl border border-border bg-surface hover:bg-surface-secondary text-content-secondary transition-colors shadow-sm">
                <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              </button>
            </div>
          </div>

          <div className="relative group w-full max-w-5xl">
            <div className="flex items-center gap-3 bg-white border border-border rounded-2xl px-5 py-3.5 hover:border-brand-300 focus-within:border-brand-400 focus-within:shadow-[0_0_20px_rgba(34,197,94,0.10)] transition-all duration-300">
              <Search className="w-5 h-5 text-content-muted flex-shrink-0" />
              <input type="text" value={searchValue} onChange={(e) => setSearchValue(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()} placeholder={`Ask something, ${userName}...`} className="flex-1 bg-transparent border-none outline-none text-sm text-content placeholder:text-content-muted font-light" />
              <button onClick={handleSearchSubmit} className="p-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white transition-colors shadow-sm">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          {kpiItems.map((kpi, i) => {
            const Icon = kpiIcons[kpi.icon] || Truck;
            return (
              <motion.div key={kpi.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06, duration: 0.4 }} className="group relative overflow-hidden bg-white border border-border rounded-2xl p-4 transition-all hover:shadow-elevated hover:border-brand-200 cursor-default">
                <div className="flex items-start justify-between relative z-10">
                  <div className="space-y-1">
                    <p className="text-[10px] text-content-secondary uppercase tracking-widest font-semibold">{t(kpi.label)}</p>
                    <p className="text-2xl font-bold text-content tracking-tight">{kpi.value}</p>
                  </div>
                  <div className="p-2 rounded-xl bg-surface-tertiary border border-border/50 group-hover:scale-110 transition-transform">
                    <Icon className="w-4 h-4" style={{ color: kpi.color }} strokeWidth={2} />
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* ═══════════ OPERATIONS ENGINE ═══════════ */}
        <div className="mt-6">
          <OperationsEngine />
        </div>

        {/* ═══════════ FINANCIAL OVERVIEW & MAP ═══════════ */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-6">
          <div className="lg:col-span-5 h-[540px]">
            <div className="w-full h-full bg-white border border-border rounded-2xl p-6 shadow-sm flex flex-col">
              <h3 className="text-sm font-semibold text-content-secondary uppercase tracking-widest mb-6">
                {t("Financial Overview")}
              </h3>
              
              <div className="space-y-6 flex-1">
                <div className="flex items-center justify-between py-3 border-b border-border/50">
                  <span className="text-[13px] text-content-secondary font-medium">{t("Total Revenue")}</span>
                  <span className="text-sm font-bold text-content">₹0</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-border/50">
                  <span className="text-[13px] text-content-secondary font-medium">{t("Total Expenses")}</span>
                  <span className="text-sm font-bold text-content">₹{(dashboardData.kpis.total_expenses_month || 0).toLocaleString('en-IN')}</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-border/50">
                  <span className="text-[13px] text-content-secondary font-medium">{t("Net Profit")}</span>
                  <span className="text-sm font-bold text-content">₹0</span>
                </div>
                <div className="flex items-center justify-between py-3">
                  <span className="text-[13px] text-content-secondary font-medium">{t("Profit Margin")}</span>
                  <span className="text-sm font-bold text-content">0%</span>
                </div>
              </div>
            </div>
          </div>
          <div className="lg:col-span-7 h-[540px]">
             <FleetMap trucks={liveTrucks} />
          </div>
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="bg-white border border-border rounded-2xl p-5 shadow-card">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest">{t("Recent Activity")}</h4>
            </div>
            <div className="space-y-3">
              {dashboardData.recentActivity.slice(0, 5).map((item, i) => {
                const Icon = activityIcons[item.category] || Route;
                return (
                  <div key={item.id || i} className="flex items-start gap-3 py-1.5 group cursor-default">
                    <div className="mt-0.5 p-1.5 rounded-lg bg-surface-tertiary border border-border">
                      <Icon className="w-3.5 h-3.5 text-brand-500" strokeWidth={1.5} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] text-content font-light leading-snug">{item.title}</p>
                      <p className="text-[11px] text-content-muted mt-0.5">{item.date ? new Date(item.date).toLocaleDateString() : 'Recent'}</p>
                    </div>
                  </div>
                );
              })}
              {dashboardData.recentActivity.length === 0 && (
                <p className="text-xs text-content-muted">No recent activity.</p>
              )}
            </div>
          </div>

          <div className="bg-surface/40 backdrop-blur-md border border-border rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-[10px] font-semibold text-content-secondary uppercase tracking-widest">{t("Alerts")}</h4>
            </div>
            <div className="space-y-3">
              {alerts.slice(0, 5).map((alert, i) => (
                <div key={alert.id || i} className="flex items-start gap-3 py-1.5 cursor-pointer group">
                  <div className={cn('mt-0.5 p-1.5 rounded-lg border transition-colors', alert.severity === 'critical' ? 'bg-red-500/10 border-red-500/20' : 'bg-amber-500/10 border-amber-500/20')}>
                    <AlertTriangle className={cn('w-3.5 h-3.5', alert.severity === 'critical' ? 'text-red-500' : 'text-amber-500')} strokeWidth={1.5} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] text-content font-medium">{alert.text}</p>
                  </div>
                </div>
              ))}
              {alerts.length === 0 && (
                <p className="text-xs text-content-muted">No active alerts.</p>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
