import { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  SlidersHorizontal,
  Download,
  Plus,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { OpportunityCard } from './OpportunityCard';
import { OpportunityFilters } from './OpportunityFilters';
import { OpportunityStats } from './OpportunityStats';
import { OpportunitySkeleton, OpportunityStatsSkeleton } from './OpportunitySkeleton';
import { OpportunityEmptyState } from './OpportunityEmptyState';
import { OpportunityErrorState } from './OpportunityErrorState';
import { OpportunityDrawer } from './OpportunityDrawer';
import { OpportunitySidebar } from './OpportunitySidebar';

import {
  fetchOpportunities,
  fetchOpportunityById,
  acceptOpportunity,
  rejectOpportunity,
  negotiateOpportunity,
  exportOpportunities,
  assignTruck,
} from '@/services/opportunities';
import { getRecentActions } from '@/api/dashboardApi';

const EMPTY_FILTERS = {
  search: '',
  vehicleType: '',
  source: '',
  status: '',
  dateFrom: '',
  dateTo: '',
  priceMin: '',
  priceMax: '',
  distanceMin: '',
  distanceMax: '',
};

/**
 * OpportunityFeedPage — Main page component.
 * Renders the complete opportunity feed with header, filters, stats, card grid,
 * detail drawer, and sidebar.
 */
export default function OpportunityFeedPage() {
  // ─── State ─────────────────────────────────────────
  const [opportunities, setOpportunities] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [filters, setFilters] = useState({ ...EMPTY_FILTERS });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFilters, setShowFilters] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);

  // ─── Data Fetching ─────────────────────────────────
  const loadData = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const [result, activityData] = await Promise.all([
        fetchOpportunities(filters),
        getRecentActions().catch(() => []),
      ]);
      setOpportunities(result.data);
      setRecentActivity(activityData);
    } catch (err) {
      setError(err.message || 'Failed to load opportunities');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ─── Computed Stats ────────────────────────────────
  const stats = {
    total: opportunities.length,
    todayNew: opportunities.filter((o) => {
      const posted = new Date(o.postedAt);
      const today = new Date();
      return posted.toDateString() === today.toDateString();
    }).length,
    highPriority: opportunities.filter((o) => o.priority === 'high').length,
    acceptedToday: opportunities.filter((o) => {
      return o.status === 'accepted';
    }).length,
  };

  // ─── Actions ───────────────────────────────────────
  const handleRefresh = () => loadData(true);

  const handleResetFilters = () => {
    setFilters({ ...EMPTY_FILTERS });
  };

  const handleViewDetails = async (opportunity) => {
    try {
      // TODO: Fetch full details from API
      const detailed = await fetchOpportunityById(opportunity.id);
      setSelectedOpportunity(detailed);
      setDrawerOpen(true);
    } catch {
      // Fallback to card data
      setSelectedOpportunity(opportunity);
      setDrawerOpen(true);
    }
  };

  const handleAccept = async (id) => {
    // TODO: POST /api/opportunities/accept
    try {
      await acceptOpportunity(id);
      // TODO: Show toast notification
      // toast.success('Opportunity Accepted', 'The opportunity has been accepted.');
      loadData(true);
      setDrawerOpen(false);
    } catch (err) {
      // TODO: Show error toast
      console.error('Accept failed:', err);
    }
  };

  const handleReject = async (id) => {
    // TODO: POST /api/opportunities/reject
    try {
      await rejectOpportunity(id);
      // TODO: Show toast notification
      loadData(true);
      setDrawerOpen(false);
    } catch (err) {
      console.error('Reject failed:', err);
    }
  };

  const handleNegotiate = async (id) => {
    // TODO: POST /api/opportunities/negotiate
    try {
      await negotiateOpportunity(id);
      // TODO: Show toast notification
      loadData(true);
    } catch (err) {
      console.error('Negotiate failed:', err);
    }
  };

  const handleExport = async () => {
    // TODO: GET /api/opportunities/export
    try {
      const blob = await exportOpportunities(filters);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'opportunities.csv';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const handleAssignTruck = async (id) => {
    // TODO: POST /api/opportunities/:id/assign-truck
    // TODO: Open truck assignment modal
    try {
      await assignTruck(id, 'TRUCK-001'); // Placeholder truck ID
      // TODO: Show toast notification
      loadData(true);
      setDrawerOpen(false);
    } catch (err) {
      console.error('Assign truck failed:', err);
    }
  };

  const handleCreateOpportunity = () => {
    // TODO: Navigate to create opportunity form or open modal
    // TODO: POST /api/opportunities/create
    console.log('Create opportunity clicked');
  };

  // ─── Render ────────────────────────────────────────
  return (
    <div className="min-h-screen animate-fade-in">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-content tracking-tight">
            Opportunity Feed
          </h1>
          <p className="text-sm text-content-secondary mt-1">
            Discover and manage available freight opportunities.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />}
            onClick={handleRefresh}
            loading={refreshing}
            id="opp-refresh-btn"
          >
            Refresh
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={<SlidersHorizontal className="h-4 w-4" />}
            onClick={() => setShowFilters(!showFilters)}
            id="opp-filters-toggle-btn"
          >
            Filters
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download className="h-4 w-4" />}
            onClick={handleExport}
            id="opp-export-btn"
          >
            Export
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={<Plus className="h-4 w-4" />}
            onClick={handleCreateOpportunity}
            id="opp-create-btn"
          >
            Create Opportunity
          </Button>
        </div>
      </div>

      {/* Filter bar */}
      {showFilters && (
        <div className="mb-6">
          <OpportunityFilters
            filters={filters}
            onChange={setFilters}
            onReset={handleResetFilters}
          />
        </div>
      )}

      {/* Stats */}
      <div className="mb-6">
        {loading ? (
          <OpportunityStatsSkeleton />
        ) : (
          <OpportunityStats data={stats} />
        )}
      </div>

      {/* Main content + sidebar layout */}
      <div className="flex gap-6">
        {/* Feed */}
        <div className="flex-1 min-w-0">
          {/* Loading */}
          {loading && <OpportunitySkeleton count={6} />}

          {/* Error */}
          {!loading && error && (
            <OpportunityErrorState
              message={error}
              onRetry={() => loadData()}
            />
          )}

          {/* Empty */}
          {!loading && !error && opportunities.length === 0 && (
            <OpportunityEmptyState onReset={handleResetFilters} />
          )}

          {/* Cards grid */}
          {!loading && !error && opportunities.length > 0 && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                {opportunities.map((opp, i) => (
                  <OpportunityCard
                    key={opp.id}
                    opportunity={opp}
                    index={i}
                    onViewDetails={handleViewDetails}
                    onAccept={handleAccept}
                    onNegotiate={handleNegotiate}
                    onReject={handleReject}
                  />
                ))}
              </div>

              {/* Pagination placeholder */}
              {/* TODO: Implement infinite scroll or pagination */}
              {/* TODO: GET /api/opportunities?page=N&limit=M */}
              <div className="flex items-center justify-center py-8">
                <p className="text-xs text-content-muted">
                  Showing {opportunities.length} of {opportunities.length} opportunities
                </p>
              </div>
            </>
          )}
        </div>

        {/* Right sidebar — hidden on small screens */}
        <div className="hidden xl:block w-[300px] flex-shrink-0 sticky top-6 self-start">
          <OpportunitySidebar
            opportunities={opportunities}
            recentActivity={recentActivity}
          />
        </div>
      </div>

      {/* Detail drawer */}
      <OpportunityDrawer
        opportunity={selectedOpportunity}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onAccept={handleAccept}
        onReject={handleReject}
        onAssignTruck={handleAssignTruck}
      />
    </div>
  );
}
