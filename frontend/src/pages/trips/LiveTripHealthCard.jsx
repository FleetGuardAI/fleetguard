import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Loader } from '@/components/ui/Loader';
import { getLiveTripIntelligence } from '@/api/tripApi';
import { Activity, AlertTriangle, TrendingDown, Clock, Route, IndianRupee } from 'lucide-react';

export default function LiveTripHealthCard({ tripId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLiveHealth = async () => {
      try {
        const result = await getLiveTripIntelligence(tripId);
        setData(result);
      } catch (err) {
        setError("Failed to load live health data.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchLiveHealth();
    
    // Poll every 5 minutes
    const interval = setInterval(fetchLiveHealth, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [tripId]);

  if (loading) {
    return (
      <Card className="animate-pulse flex items-center justify-center py-12">
        <Loader size="md" />
      </Card>
    );
  }

  if (error || !data) {
    return null; // Silent fail, just don't show the card
  }

  // Determine styles based on health
  const isCritical = data.health_status === 'CRITICAL';
  const isAtRisk = data.health_status === 'AT_RISK';
  const headerBg = isCritical ? 'bg-red-500' : isAtRisk ? 'bg-amber-500' : 'bg-green-500';
  const headerText = 'text-white';

  return (
    <Card className="overflow-hidden border border-border mt-6">
      <div className={`${headerBg} ${headerText} px-4 py-3 flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          <h3 className="font-semibold tracking-wide">Live Trip Health</h3>
        </div>
        <div className="font-bold uppercase text-sm tracking-wider px-2 py-0.5 bg-white/20 rounded">
          {data.health_status.replace('_', ' ')}
        </div>
      </div>
      
      <div className="p-4 space-y-5">
        {!data.snapshot_available && (
          <div className="text-sm text-amber-600 bg-amber-50 dark:bg-amber-900/20 p-2 rounded">
            Pre-trip snapshot unavailable. Live health calculations are limited.
          </div>
        )}

        {/* Profit Projection */}
        {data.expected_profit !== null && (
          <div className="bg-surface-elevated rounded-lg p-4 border border-border">
            <h4 className="text-xs font-semibold text-content-secondary uppercase mb-3 flex items-center gap-1.5">
              <IndianRupee className="h-4 w-4" /> Projected Economics
            </h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-content-secondary">Expected Profit</div>
                <div className="font-medium text-lg">₹{data.expected_profit.toLocaleString()}</div>
              </div>
              
              <div>
                <div className="text-sm text-content-secondary">Current Projection</div>
                <div className={`font-bold text-lg ${data.profit_erosion > 0 ? 'text-red-500' : 'text-green-500'}`}>
                  ₹{data.projected_profit?.toLocaleString() || '---'}
                </div>
              </div>
            </div>
            
            {data.profit_erosion > 0 && (
              <div className="mt-3 pt-3 border-t border-border flex items-center justify-between">
                <div className="text-sm text-red-500 flex items-center gap-1">
                  <TrendingDown className="h-4 w-4" /> Profit Erosion
                </div>
                <div className="font-medium text-red-500">
                  -₹{data.profit_erosion.toLocaleString()} ({data.profit_erosion_pct?.toFixed(1)}%)
                </div>
              </div>
            )}
          </div>
        )}

        {/* Live Deviations */}
        {data.deviations.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-content-secondary uppercase mb-3 flex items-center gap-1.5">
              <AlertTriangle className="h-4 w-4" /> Active Deviations
            </h4>
            <div className="space-y-2">
              {data.deviations.map((dev, idx) => (
                <div key={idx} className={`p-3 rounded border text-sm flex justify-between items-start ${
                  dev.severity === 'CRITICAL' ? 'bg-red-500/10 border-red-500/20 text-red-700 dark:text-red-400' : 
                  'bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400'
                }`}>
                  <div>
                    <span className="font-semibold mr-2">{dev.metric}:</span>
                    <span>{dev.description}</span>
                  </div>
                  <span className="font-bold">{dev.variance_pct > 0 ? '+' : ''}{dev.variance_pct?.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Progress Stats */}
        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-border">
            <div>
              <div className="flex items-center gap-1.5 text-xs text-content-secondary mb-1">
                <Clock className="h-3.5 w-3.5" /> Elapsed Time
              </div>
              <div className="font-medium text-content">{data.elapsed_hours?.toFixed(1) || '--'} hrs</div>
              {data.estimated_remaining_hours && (
                <div className="text-xs text-content-muted mt-0.5">{data.estimated_remaining_hours.toFixed(1)} hrs left est.</div>
              )}
            </div>
            
            <div>
              <div className="flex items-center gap-1.5 text-xs text-content-secondary mb-1">
                <IndianRupee className="h-3.5 w-3.5" /> Cost So Far
              </div>
              <div className="font-medium text-content">₹{data.actual_cost_so_far?.toLocaleString() || '0'}</div>
              {data.projected_total_cost && (
                <div className="text-xs text-content-muted mt-0.5">₹{data.projected_total_cost.toLocaleString()} total est.</div>
              )}
            </div>
        </div>

      </div>
    </Card>
  );
}
