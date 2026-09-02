import React, { useState, useEffect } from 'react';
import { Navigation, MapPin, Compass, ShieldAlert, Route, Clock, Zap, CheckCircle2 } from 'lucide-react';
import api from '@/api/client';
import { cn } from '@/utils/cn';

export default function NavigationPage() {
  const [trips, setTrips] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadTrips() {
      try {
        const data = await api.trips.list({ status: 'IN_PROGRESS', limit: 10 });
        setTrips(data || []);
        if (data && data.length > 0) {
          setSelectedRoute(data[0]);
        }
      } catch (error) {
        console.error('Failed to load active trips:', error);
      } finally {
        setLoading(false);
      }
    }
    loadTrips();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-border shadow-sm">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 block mb-1">
            Live Route Guidance & GPS
          </span>
          <h1 className="text-2xl font-bold text-content tracking-tight">
            Fleet Navigation
          </h1>
        </div>

        <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 px-3 py-1.5 rounded-xl border border-emerald-200 dark:border-emerald-800 text-xs font-bold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Live GPS Telemetry Connected
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Navigation Map Card */}
        <div className="lg:col-span-8 bg-white dark:bg-slate-900 rounded-2xl border border-border shadow-sm overflow-hidden flex flex-col h-[520px] relative">
          {/* Simulated Map Visual Canvas */}
          <div className="absolute inset-0 bg-slate-950 flex flex-col items-center justify-center p-6 text-center text-white overflow-hidden">
            {/* Map Grid Pattern background */}
            <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:16px_16px]" />

            {loading ? (
               <div className="relative z-10 text-slate-400">Loading active routes...</div>
            ) : !selectedRoute ? (
               <div className="relative z-10 text-slate-400">No active routes currently.</div>
            ) : (
              <>
                {/* Glowing route line */}
                <div className="w-full h-1 bg-gradient-to-r from-emerald-500 via-brand-500 to-amber-500 relative my-8 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.8)]">
                  <div className="absolute -top-3 left-1/4 w-7 h-7 rounded-full bg-emerald-500 flex items-center justify-center shadow-lg border-2 border-white animate-bounce">
                    <Navigation className="w-4 h-4 text-white transform rotate-45" />
                  </div>
                  <div className="absolute -top-2 left-0 w-5 h-5 rounded-full bg-emerald-500 border-2 border-white" />
                  <div className="absolute -top-2 right-0 w-5 h-5 rounded-full bg-red-500 border-2 border-white" />
                </div>

                <div className="relative z-10 space-y-2 bg-slate-900/90 backdrop-blur-md p-5 rounded-2xl border border-slate-800 max-w-md">
                  <span className="text-[10px] uppercase tracking-widest text-brand-400 font-bold">Current Active Route</span>
                  <h3 className="text-xl font-bold text-white">{selectedRoute.start_location} to {selectedRoute.end_location}</h3>
                  <p className="text-xs text-slate-400">Trip ID: <span className="text-white font-bold">{selectedRoute.id}</span></p>
                  
                  <div className="flex items-center justify-around pt-3 border-t border-slate-800 text-xs">
                    <div>
                      <span className="text-slate-400 text-[10px] block">Progress</span>
                      <span className="font-bold text-emerald-400">
                        {selectedRoute.actual_distance && selectedRoute.planned_distance 
                          ? Math.round((selectedRoute.actual_distance / selectedRoute.planned_distance) * 100) 
                          : 0}%
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Distance</span>
                      <span className="font-bold text-white">{selectedRoute.planned_distance || 0} km</span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] block">Status</span>
                      <span className="font-bold text-brand-400">{selectedRoute.status}</span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Route Selectors & Timeline */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-border shadow-sm space-y-3">
            <h3 className="font-bold text-content text-base border-b border-border pb-2">Active Navigation Routes</h3>

            <div className="space-y-2 max-h-[420px] overflow-y-auto">
              {!loading && trips.length === 0 && (
                 <p className="text-sm text-content-muted">No active trips found.</p>
              )}
              {trips.map((trip) => (
                <div
                  key={trip.id}
                  onClick={() => setSelectedRoute(trip)}
                  className={cn(
                    "p-3.5 rounded-xl border transition-all cursor-pointer",
                    selectedRoute?.id === trip.id
                      ? "bg-brand-500/10 border-brand-500 dark:bg-brand-900/20"
                      : "bg-surface-secondary border-border hover:border-brand-300"
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="font-bold text-content text-sm truncate max-w-[150px]">{trip.start_location}</h4>
                    <span className="text-[10px] font-bold text-emerald-600">
                       {trip.status}
                    </span>
                  </div>
                  <p className="text-xs text-content-muted truncate">{trip.end_location}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
