import React, { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import KPICards from '../components/dashboard/KPICards';
import MapPanel from '../components/dashboard/MapPanel';
import ActionQueue from '../components/dashboard/ActionQueue';
import DriverTable from '../components/dashboard/DriverTable';
import FuelChart from '../components/dashboard/FuelChart';
import { getDashboardData } from '@/api/dashboardApi';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { ErrorState } from '@/components/shared/ErrorState';

export default function DashboardOverview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { error, success } = useToast();

  const loadData = async (isSilent = false) => {
    if (isSilent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const res = await getDashboardData();
      setData(res);
    } catch (err) {
      setData(null);
      error('Data Load Error', 'Failed to retrieve fresh dashboard metrics.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApprove = (ticketId) => {
    setData(prev => {
      if (!prev) return prev;
      const updatedActivity = prev.recentActivity.map(t =>
        t.id === ticketId ? { ...t, status: 'approved' } : t
      );
      success('Claim Approved', `Approved repair ticket #${ticketId}`);
      return { ...prev, recentActivity: updatedActivity };
    });
  };

  const handleReject = (ticketId) => {
    setData(prev => {
      if (!prev) return prev;
      const updatedActivity = prev.recentActivity.map(t =>
        t.id === ticketId ? { ...t, status: 'rejected' } : t
      );
      error('Claim Rejected', `Rejected repair ticket #${ticketId}`);
      return { ...prev, recentActivity: updatedActivity };
    });
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="h-6 w-48 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
          <div className="h-10 w-28 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <div className="h-96 bg-surface border border-border rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!data) {
    return (
      <ErrorState
        title="Failed to Load Operations Dashboard"
        message="Please check your connection and try again."
        onRetry={() => loadData()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Title Header with Refresh action */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-content">Fleet Operations</h1>
          <p className="text-sm text-content-secondary">Real-time status updates and action alerts.</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => loadData(true)}
          loading={refreshing}
          icon={<RefreshCw className="h-4 w-4" />}
        >
          Refresh
        </Button>
      </div>

      {/* Metric Cards */}
      <KPICards kpis={data?.kpis} />

      {/* Map telemetry */}
      <div className="w-full">
        <MapPanel />
      </div>

      {/* Charts & Actions Row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3">
          <FuelChart data={data?.fuelChart || []} />
        </div>
        <div className="lg:col-span-2">
          <ActionQueue
            tickets={data?.recentActivity || []}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        </div>
      </div>

      {/* Driver safety scoring table */}
      <DriverTable drivers={data?.flaggedDrivers || []} />
    </div>
  );
}
