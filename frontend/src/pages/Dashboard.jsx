import React, { useState } from 'react';
import { ShieldCheck, Search, Bell, RefreshCw } from 'lucide-react';

import Sidebar from '../components/dashboard/Sidebar';
import KPICards from '../components/dashboard/KPICards';
import MapPanel from '../components/dashboard/MapPanel';
import ActionQueue from '../components/dashboard/ActionQueue';
import DriverTable from '../components/dashboard/DriverTable';
import FuelChart from '../components/dashboard/FuelChart';

import { mockTickets, mockDrivers, generateMockFuelData } from '../data/mockData';

/**
 * Redesigned Owner BI Dashboard page
 * Align layout to match the monitor screen:
 * - Left slim sidebar
 * - Top Metrics header row
 * - Core content pane (Map, Action Queue, Driver metrics)
 */
export default function Dashboard() {
  const [tickets, setTickets] = useState(mockTickets);
  const [drivers, setDrivers] = useState(mockDrivers);
  const [fuelData] = useState(generateMockFuelData());
  const [isLoading, setIsLoading] = useState(false);

  const handleApprove = (ticketId) => {
    setTickets((prev) =>
      prev.map((t) => (t.id === ticketId ? { ...t, status: 'approved' } : t))
    );
  };

  const handleReject = (ticketId) => {
    setTickets((prev) =>
      prev.map((t) => (t.id === ticketId ? { ...t, status: 'rejected' } : t))
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex">
      {/* Slim left navigation panel */}
      <Sidebar />

      {/* Main dashboard viewport */}
      <div className="flex-1 pl-16 flex flex-col min-w-0">
        
        {/* Top Header */}
        <header className="h-14 px-6 flex items-center justify-between border-b border-slate-200 bg-white/90 backdrop-blur-xl shrink-0 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">FleetFlow</span>
            <span className="text-slate-300">/</span>
            <span className="text-xs font-semibold text-slate-900">Fleet Dashboard</span>
          </div>

          {/* Right Header actions */}
          <div className="flex items-center gap-4">
            <div className="relative hidden md:flex items-center">
              <Search className="absolute left-2.5 w-3.5 h-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search vehicles, drivers..."
                className="w-48 pl-8 pr-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-900 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <button
              onClick={() => {
                setIsLoading(true);
                setTimeout(() => setIsLoading(false), 500);
              }}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-emerald-600 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>

            <button className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-emerald-600 transition-colors relative notification-dot">
              <Bell className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-2 border-l border-slate-200 pl-4 ml-2">
              <div className="w-7 h-7 rounded-full bg-emerald-600 flex items-center justify-center text-[10px] font-bold text-white shadow-sm">
                SC
              </div>
              <span className="text-[11px] font-medium text-slate-700">Suryansh Chaudhary</span>
            </div>
          </div>
        </header>

        {/* Dashboard Grid Pane */}
        <div className="p-6 space-y-6 flex-1 min-h-0 overflow-y-auto bg-grid">
          
          {/* Top KPI widgets */}
          <KPICards />

          {/* Core Row: Map panel */}
          <div className="w-full">
            <MapPanel />
          </div>

          {/* Bottom Row: Charts & Verifications */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3">
              <FuelChart data={fuelData} />
            </div>
            <div className="lg:col-span-2">
              <ActionQueue
                tickets={tickets}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            </div>
          </div>

          {/* Driver scoring row */}
          <DriverTable drivers={drivers} />

        </div>
      </div>
    </div>
  );
}
