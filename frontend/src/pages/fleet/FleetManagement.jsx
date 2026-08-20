import React, { useState, useEffect } from 'react';
import {
  Truck, Users, FileText, CreditCard, DollarSign, Calendar, AlertTriangle, CheckCircle2,
  Clock, ShieldAlert, ArrowUpRight, Search, ChevronRight, Wrench, Download, BadgeCheck
} from 'lucide-react';
import { getVehicles } from '@/api/vehicleApi';
import { getDrivers } from '@/api/driverApi';
import { getLiveTracking } from '@/api/telematicsApi';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { Badge } from '@/components/ui/Badge';
import { Table } from '@/components/ui/Table';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/utils/cn';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';

export default function FleetManagement() {
  const { error: toastError } = useToast();
  const [activeTab, setActiveTab] = useState('trucks'); // 'trucks' or 'drivers'
  const [searchQuery, setSearchQuery] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [liveLocations, setLiveLocations] = useState([]);

  const [selectedTruckId, setSelectedTruckId] = useState(null);
  const [selectedDriverId, setSelectedDriverId] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [vehiclesData, driversData, trackingData] = await Promise.all([
        getVehicles(),
        getDrivers(),
        getLiveTracking().catch(() => []),
      ]);
      setVehicles(vehiclesData);
      setDrivers(driversData);
      setLiveLocations(trackingData);

      if (vehiclesData && vehiclesData.length > 0) {
        setSelectedTruckId(vehiclesData[0].id);
      }
      if (driversData && driversData.length > 0) {
        setSelectedDriverId(driversData[0].id);
      }
    } catch (err) {
      console.error(err);
      setError(err);
      toastError('Load Error', 'Failed to retrieve fleet data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return <div className="p-12 text-center"><Loader className="mx-auto" /></div>;
  }

  if (error) {
    return <ErrorState message="Failed to load fleet data" onRetry={loadData} />;
  }

  const selectedTruck = vehicles.find((t) => t.id === selectedTruckId) || vehicles[0] || {};
  const selectedDriver = drivers.find((d) => d.id === selectedDriverId) || drivers[0] || {};

  const filteredTrucks = vehicles.filter((t) =>
    (t.license_plate || t.registration_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (t.make || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (t.model || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredDrivers = drivers.filter((d) =>
    (d.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (d.phone_number || '').includes(searchQuery)
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* ─── HEADER & TAB SWITCHER ─── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-border shadow-sm">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 block mb-1">
            Fleet Operations Hub
          </span>
          <h1 className="text-2xl font-bold text-content tracking-tight">
            Trucks & Drivers Details
          </h1>
        </div>

        {/* Tab switcher: Trucks vs Drivers */}
        <div className="flex items-center bg-surface-secondary p-1 rounded-xl border border-border">
          <button
            onClick={() => { setActiveTab('trucks'); setSearchQuery(''); }}
            className={cn(
              'flex items-center gap-2 px-5 py-2.5 rounded-lg font-bold text-sm transition-all',
              activeTab === 'trucks'
                ? 'bg-brand-600 text-white shadow-md'
                : 'text-content-secondary hover:text-content'
            )}
          >
            <Truck className="w-4 h-4" />
            Truck Details
          </button>
          <button
            onClick={() => { setActiveTab('drivers'); setSearchQuery(''); }}
            className={cn(
              'flex items-center gap-2 px-5 py-2.5 rounded-lg font-bold text-sm transition-all',
              activeTab === 'drivers'
                ? 'bg-brand-600 text-white shadow-md'
                : 'text-content-secondary hover:text-content'
            )}
          >
            <Users className="w-4 h-4" />
            Driver Details
          </button>
        </div>
      </div>

      {/* ─── TRUCKS TAB CONTENT ─── */}
      {activeTab === 'trucks' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Truck Selector Sidebar */}
          <div className="lg:col-span-4 space-y-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3.5 text-content-muted" />
              <input
                type="text"
                placeholder="Search truck number, make..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 text-sm bg-white dark:bg-slate-900 border border-border rounded-xl text-content placeholder:text-content-muted focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {filteredTrucks.map((truck) => {
                const isSelected = truck.id === selectedTruck.id;
                return (
                  <div
                    key={truck.id}
                    onClick={() => setSelectedTruckId(truck.id)}
                    className={cn(
                      'p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between',
                      isSelected
                        ? 'bg-brand-500/10 border-brand-500 dark:bg-brand-900/20 shadow-sm'
                        : 'bg-white dark:bg-slate-900 border-border hover:border-brand-300'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        'p-2.5 rounded-lg border',
                        isSelected ? 'bg-brand-600 text-white border-brand-600' : 'bg-surface-secondary text-content-secondary border-border'
                      )}>
                        <Truck className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="font-bold text-content text-sm">{truck.license_plate || truck.registration_number}</h4>
                        <p className="text-xs text-content-muted">{truck.make} {truck.model}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                        {truck.status || 'Active'}
                      </span>
                      <ChevronRight className={cn("w-4 h-4 ml-auto mt-1 transition-transform", isSelected && "rotate-90 text-brand-600")} />
                    </div>
                  </div>
                );
              })}
              {filteredTrucks.length === 0 && (
                <div className="p-4 text-center text-content-muted text-sm border border-dashed rounded-xl">No trucks found.</div>
              )}
            </div>
          </div>

          {/* Truck Full Details */}
          {selectedTruck.id && (
            <div className="lg:col-span-8 space-y-6">
              {/* Truck Overview Header */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-border shadow-sm relative overflow-hidden">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h2 className="text-2xl font-black text-content">{selectedTruck.license_plate || selectedTruck.registration_number}</h2>
                      <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-brand-100 dark:bg-brand-900/40 text-brand-700 dark:text-brand-300">
                        {selectedTruck.year || 'N/A'}
                      </span>
                    </div>
                    <p className="text-sm text-content-muted">{selectedTruck.make || 'Unknown'} — {selectedTruck.model || 'Unknown'} ({selectedTruck.tank_capacity || 0}L Tank Capacity)</p>
                  </div>

                  <div className="flex items-center gap-3 bg-surface-secondary p-3 rounded-xl border border-border">
                    <DollarSign className="w-5 h-5 text-emerald-600" />
                    <div>
                      <span className="text-[10px] uppercase font-bold text-content-muted">Total Expenses Incurred</span>
                      <h3 className="text-lg font-bold text-emerald-600">{formatCurrency(selectedTruck.total_expenses_done || 0)}</h3>
                    </div>
                  </div>
                </div>
              </div>

              {/* ─── EMI DETAILS CARD ─── */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-border shadow-sm">
                <div className="flex items-center justify-between mb-4 border-b border-border pb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600">
                      <CreditCard className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-content text-base">Truck EMI & Loan Breakdown</h3>
                      <p className="text-xs text-content-muted">{selectedTruck.emi?.bank || 'HDFC Bank Commercial Auto'}</p>
                    </div>
                  </div>
                  <span className="px-3 py-1 text-xs font-bold rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
                    {selectedTruck.emi?.status || 'Active EMI'}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-5">
                  <div className="bg-surface-secondary p-3 rounded-xl border border-border">
                    <span className="text-[11px] font-semibold text-content-muted block mb-0.5">Total Loan Amount</span>
                    <p className="text-base font-bold text-content">{formatCurrency(selectedTruck.emi?.total_loan || 0)}</p>
                  </div>
                  <div className="bg-surface-secondary p-3 rounded-xl border border-border">
                    <span className="text-[11px] font-semibold text-content-muted block mb-0.5">Monthly EMI</span>
                    <p className="text-base font-bold text-brand-600">{formatCurrency(selectedTruck.emi?.monthly_emi || 0)}/mo</p>
                  </div>
                  <div className="bg-surface-secondary p-3 rounded-xl border border-border">
                    <span className="text-[11px] font-semibold text-content-muted block mb-0.5">EMI Paid till date</span>
                    <p className="text-base font-bold text-emerald-600">{formatCurrency(selectedTruck.emi?.emi_paid_amount || 0)}</p>
                  </div>
                  <div className="bg-surface-secondary p-3 rounded-xl border border-border">
                    <span className="text-[11px] font-semibold text-content-muted block mb-0.5">EMI Left (Remaining)</span>
                    <p className="text-base font-bold text-red-600 dark:text-red-400">{formatCurrency(selectedTruck.emi?.emi_remaining_amount || 0)}</p>
                  </div>
                </div>

                {/* EMI Progress Bar */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1 text-content-muted">
                    <span>Tenure Paid: {selectedTruck.emi?.emi_paid_months || 0} / {selectedTruck.emi?.total_months || 0} Months</span>
                    <span>Next Due: {selectedTruck.emi?.next_due_date || 'N/A'}</span>
                  </div>
                  <div className="w-full bg-surface-secondary rounded-full h-3 overflow-hidden border border-border">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                      style={{
                        width: selectedTruck.emi ? `${Math.round(((selectedTruck.emi?.emi_paid_months || 0) / (selectedTruck.emi?.total_months || 1)) * 100)}%` : '0%',
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* ─── MAINTENANCE WORK STATUS ─── */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-border shadow-sm">
                <div className="flex items-center justify-between mb-4 border-b border-border pb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-purple-500/10 text-purple-600">
                      <Wrench className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-bold text-content text-base">Vehicle Servicing & Work Required</h3>
                      <p className="text-xs text-content-muted">Maintenance health and pending garage tasks</p>
                    </div>
                  </div>
                </div>

                {selectedTruck.maintenance_status?.work_required ? (
                  <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-2 font-bold text-amber-800 dark:text-amber-300 text-sm">
                        <AlertTriangle className="w-4 h-4 text-amber-600" /> Servicing Work Required
                      </span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded bg-amber-200 dark:bg-amber-800 text-amber-900 dark:text-amber-100">
                        Est Cost: {formatCurrency(selectedTruck.maintenance_status.estimated_cost)}
                      </span>
                    </div>
                    <ul className="list-disc list-inside text-xs text-amber-900 dark:text-amber-200 space-y-1">
                      {selectedTruck.maintenance_status.pending_tasks.map((task, idx) => (
                        <li key={idx} className="font-medium">{task}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-900/10 border border-emerald-200 dark:border-emerald-800 flex items-center gap-3 text-emerald-800 dark:text-emerald-300 text-sm font-semibold">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    No pending maintenance work required on this truck. Vehicle is healthy and road-ready.
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─── DRIVERS TAB CONTENT ─── */}
      {activeTab === 'drivers' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Driver Selector Sidebar */}
          <div className="lg:col-span-4 space-y-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3.5 text-content-muted" />
              <input
                type="text"
                placeholder="Search driver name, mobile..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 text-sm bg-white dark:bg-slate-900 border border-border rounded-xl text-content placeholder:text-content-muted focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {filteredDrivers.map((driver) => {
                const isSelected = driver.id === selectedDriver.id;
                return (
                  <div
                    key={driver.id}
                    onClick={() => setSelectedDriverId(driver.id)}
                    className={cn(
                      'p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between',
                      isSelected
                        ? 'bg-brand-500/10 border-brand-500 dark:bg-brand-900/20 shadow-sm'
                        : 'bg-white dark:bg-slate-900 border-border hover:border-brand-300'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        'w-10 h-10 rounded-xl font-bold flex items-center justify-center text-sm',
                        isSelected ? 'bg-brand-600 text-white' : 'bg-surface-secondary text-content-secondary'
                      )}>
                        {(driver.name || '?').charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-bold text-content text-sm">{driver.name || 'Unnamed Driver'}</h4>
                        <p className="text-xs text-content-muted">{driver.phone_number}</p>
                      </div>
                    </div>
                    <ChevronRight className={cn("w-4 h-4 transition-transform", isSelected && "rotate-90 text-brand-600")} />
                  </div>
                );
              })}
              {filteredDrivers.length === 0 && (
                <div className="p-4 text-center text-content-muted text-sm border border-dashed rounded-xl">No drivers found.</div>
              )}
            </div>
          </div>

          {/* Driver Full Details */}
          {selectedDriver.id && (
            <div className="lg:col-span-8 space-y-6">
              {/* Driver Profile Header */}
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-border shadow-sm">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-brand-600 text-white font-black text-xl flex items-center justify-center shadow-lg">
                      {(selectedDriver.name || '?').charAt(0)}
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-content">{selectedDriver.name || 'Unnamed Driver'}</h2>
                      <p className="text-sm text-content-muted font-mono">{selectedDriver.phone_number}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-center px-4 py-2 bg-surface-secondary rounded-xl border border-border">
                      <span className="text-[10px] font-bold text-content-muted block uppercase">Rating</span>
                      <span className="text-base font-bold text-amber-500">★ {selectedDriver.rating || 0}</span>
                    </div>
                    <div className="text-center px-4 py-2 bg-surface-secondary rounded-xl border border-border">
                      <span className="text-[10px] font-bold text-content-muted block uppercase">Total Trips</span>
                      <span className="text-base font-bold text-brand-600">{selectedDriver.total_trips || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
