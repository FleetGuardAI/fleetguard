import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  Bell,
} from 'lucide-react';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/utils/cn';
import {
  OpportunityFeed,
  FleetHealthSidebar,
  AiDashboardCharts,
  FleetHealthRail,
} from './dashboard-ai';
import {
  fetchAiOpportunities,
  assignOpportunity,
  dismissOpportunity,
  scheduleOpportunity,
} from '@/services/aiOpportunities';
import {
  MOCK_FLEET_HEALTH,
  MOCK_UPCOMING_ALERTS,
  MOCK_RECENT_AI_ACTIONS,
} from '@/data/aiOpportunityData';
import { useLanguage } from '@/i18n/LanguageContext';
import { WeatherIndicatorCard } from './opportunities/WeatherIndicatorCard';

export default function DashboardOverview() {
  const { t } = useLanguage();
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [health, setHealth] = useState(MOCK_FLEET_HEALTH);
  const [alerts, setAlerts] = useState(MOCK_UPCOMING_ALERTS);
  const [actions, setActions] = useState(MOCK_RECENT_AI_ACTIONS);
  
  const { success, error, info } = useToast();

  const loadData = async (isSilent = false) => {
    if (isSilent) setRefreshing(true);
    else setLoading(true);

    try {
      const res = await fetchAiOpportunities();
      setOpportunities(res.data);
    } catch (err) {
      error('Data Load Error', 'Failed to retrieve operational signals.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // ─── Actions ─────────────────────────────────────────────────────────────
  
  const handleAssign = async (id) => {
    try {
      await assignOpportunity(id);
      success('Signal Resolved', `Initiated resolution protocol for ${id}`);
      setOpportunities(prev => prev.map(o => o.id === id ? { ...o, status: 'assigned' } : o));
      setActions(prev => [
        { id: Date.now(), action: `Resolved anomaly signal ${id}`, time: 'Just now' },
        ...prev
      ]);
    } catch (err) {
      error('Resolution Failed', 'Could not execute the assignment.');
    }
  };

  const handleDismiss = async (id) => {
    try {
      await dismissOpportunity(id);
      info('Signal Dismissed', `${id} archived successfully.`);
      setOpportunities(prev => prev.filter(o => o.id !== id));
    } catch (err) {
      error('Action Failed', 'Could not archive the signal.');
    }
  };

  const handleSchedule = async (id) => {
    try {
      await scheduleOpportunity(id);
      success('Audit Scheduled', `Scheduled follow-up evaluation for ${id}`);
      setOpportunities(prev => prev.map(o => o.id === id ? { ...o, status: 'scheduled' } : o));
    } catch (err) {
      error('Action Failed', 'Could not schedule follow-up.');
    }
  };

  const handleInvestigate = (id) => {
    info('Diagnostics Loaded', `Loaded full telematics log workspace for ${id}`);
  };

  const activeOpportunities = opportunities.filter(o => o.status === 'new' || o.status === 'investigating');
  const totalSavingsIdentified = activeOpportunities.reduce((sum, o) => sum + o.potentialSaving, 0);

  return (
    <div className="space-y-10 py-4 max-w-[1400px] mx-auto transition-colors duration-300">
      
      {/* ─── TOP HEADER ─── */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6 border-b border-border/40 pb-8">
        <div>
          <span className="text-[11px] font-semibold text-content-muted uppercase tracking-widest block mb-2">
            {t("Operations Workspace")}
          </span>
          <h1 className="text-3xl font-light text-content tracking-tight mb-2">
            {t("Good Morning, ")}<span className="font-medium text-brand-600 dark:text-brand-400">Rudra</span>
          </h1>
          <p className="text-sm text-content-secondary max-w-2xl leading-relaxed">
            {t("Operations Engine identified")}{' '}
            <span className="font-semibold text-content">{activeOpportunities.length} {t("signals")}</span>{' '}
            {t("saving up to")}{' '}
            <span className="font-semibold text-content">₹{totalSavingsIdentified.toLocaleString('en-IN')}</span>{' '}
            {t("this month.")}
          </p>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3 self-end md:self-start">
          <button
            onClick={() => loadData(true)}
            className="inline-flex items-center justify-center p-2 rounded-xl border border-border/50 hover:bg-surface-secondary text-content-secondary transition-colors"
            title={t("Refresh Diagnostics")}
          >
            <RefreshCw className={cn("w-4.5 h-4.5", refreshing && "animate-spin")} />
          </button>
          
          <button
            className="relative inline-flex items-center justify-center p-2 rounded-xl border border-border/50 hover:bg-surface-secondary text-content-secondary transition-colors"
            title={t("Notifications")}
          >
            <Bell className="w-4.5 h-4.5" />
          </button>
        </div>
      </div>

      {/* ─── MAIN LAYOUT ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-10 gap-10">
        
        {/* Left 70% column: Handcrafted Opportunity Feed */}
        <div className="lg:col-span-7 space-y-6">
          <OpportunityFeed
            opportunities={activeOpportunities}
            loading={loading}
            refreshing={refreshing}
            onRefresh={() => loadData(true)}
            onAssign={handleAssign}
            onSchedule={handleSchedule}
            onDismiss={handleDismiss}
            onInvestigate={handleInvestigate}
          />
        </div>

        {/* Right 30% column: Fleet Health Sidebar & Rails */}
        <div className="lg:col-span-3 space-y-8">
          <WeatherIndicatorCard />
          <FleetHealthRail health={health} />
          
          <div className="h-px bg-border/40" />
          
          <FleetHealthSidebar
            health={health}
            alerts={alerts}
            recentActions={actions}
          />
        </div>
      </div>

      {/* Separator */}
      <div className="h-px bg-border/40" />

      {/* ─── SECONDARY TRENDS SECTION ─── */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xs font-semibold text-content-muted uppercase tracking-widest">
            {t("Performance Trends")}
          </h2>
          <p className="text-xs text-content-muted mt-1">
            {t("Secondary operational metrics updated daily")}
          </p>
        </div>

        <AiDashboardCharts />
      </div>

    </div>
  );
}
