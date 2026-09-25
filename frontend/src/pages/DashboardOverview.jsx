import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle } from 'lucide-react';
import { useToast } from '@/components/ui/Toast';
import { useLanguage } from '@/i18n/LanguageContext';
import { getDashboardData, getFleetHealth, getUpcomingAlerts } from '@/api/dashboardApi';
import { getLiveTracking } from '@/api/telematicsApi';

// Command Center modules
import { CommandHeader } from './dashboard-ai/CommandHeader';
import { FleetCanvas } from './dashboard-ai/FleetCanvas';
import { IntelligencePanel } from './dashboard-ai/IntelligencePanel';
import { FleetEconomics } from './dashboard-ai/FleetEconomics';
import { FleetPulse } from './dashboard-ai/FleetPulse';

export default function DashboardOverview() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { success, error: showError, info } = useToast();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [health, setHealth] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [searchValue, setSearchValue] = useState('');
  const [fetchError, setFetchError] = useState(null);

  // Operations engine insights
  const [opsInsights, setOpsInsights] = useState([]);

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

  const loadData = async (isSilent = false) => {
    if (isSilent) setRefreshing(true);
    else setLoading(true);
    setFetchError(null);
    try {
      const [healthData, alertsData, dbData, tracking] = await Promise.all([
        getFleetHealth().catch(() => ({})),
        getUpcomingAlerts().catch(() => []),
        getDashboardData(),
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

      // Try to load operations engine insights
      try {
        const { default: api } = await import('@/api/client');
        const data = await api.operationsEngine.getInsights();
        setOpsInsights(data?.insights || []);
      } catch {
        // Operations endpoint not available — intelligence panel will use fallback
        setOpsInsights([]);
      }
    } catch (e) {
      console.error('[Dashboard] Failed to load real data:', e);
      setFetchError(e.message || 'Unable to load dashboard data. Check network connection.');
      showError(e.message || 'Unable to load dashboard data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  // Error state
  if (fetchError && !loading) {
    return (
      <div className="flex w-full min-h-full bg-surface-base items-center justify-center p-6">
        <div className="text-center space-y-4 max-w-md">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-semibold text-content">Unable to load dashboard data</h2>
          <p className="text-content-secondary text-sm">{fetchError}</p>
          <button onClick={() => loadData()} className="mt-4 px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors">
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  const handleSearchSubmit = () => {
    if (searchValue.trim()) {
      navigate('/dashboard/chatbox', { state: { initialMessage: searchValue } });
    } else {
      navigate('/dashboard/chatbox');
    }
  };

  const userName = user?.name || 'Owner';

  return (
    <div className="flex w-full bg-surface-base overflow-x-hidden animate-fade-in" style={{ minHeight: 'calc(100vh - 6rem)' }}>
      <div className="flex-1 flex flex-col px-3 lg:px-5 py-3 gap-3" style={{ height: 'calc(100vh - 6rem)' }}>

        {/* ═══════ COMMAND HEADER ═══════ */}
        <CommandHeader
          kpis={dashboardData.kpis}
          refreshing={refreshing}
          onRefresh={() => loadData(true)}
          searchValue={searchValue}
          onSearchChange={setSearchValue}
          onSearchSubmit={handleSearchSubmit}
          userName={userName}
        />

        {/* ═══════ MAIN GRID: Canvas + Intelligence ═══════ */}
        <div className="flex-1 grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-3 min-h-0">
          {/* Fleet Canvas — dark operational map */}
          <div className="min-h-[300px] xl:min-h-0">
            <FleetCanvas trucks={liveTrucks} />
          </div>

          {/* Intelligence Panel — right sidebar */}
          <div className="min-h-[300px] xl:min-h-0">
            <IntelligencePanel
              alerts={alerts}
              insights={opsInsights}
            />
          </div>
        </div>

        {/* ═══════ BOTTOM STRIP: Economics + Pulse ═══════ */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 shrink-0">
          <FleetEconomics kpis={dashboardData.kpis} />
          <FleetPulse recentActivity={dashboardData.recentActivity} />
        </div>

      </div>
    </div>
  );
}
