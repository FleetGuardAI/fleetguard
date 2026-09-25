import React, { useState, useEffect } from 'react';
import { FileText, Download, BarChart2, Calendar, FileSpreadsheet, DownloadCloud, TrendingUp, ShieldCheck, Filter, Wrench, Receipt, Truck, Route, IndianRupee, Activity, Info } from 'lucide-react';
import { getFleetReportData, exportReport } from '@/api/reportApi';
import { getVehicles } from '@/api/vehicleApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';
import { useToast } from '@/components/ui/Toast';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];
import { cn } from '@/utils/cn';

// --- Shared Custom Tooltip ---
const CustomTooltip = ({ active, payload, label, formatter }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="bg-white/95 backdrop-blur-sm border border-slate-200 shadow-md rounded-lg p-3 min-w-[120px]">
        {label && <p className="text-xs font-semibold text-slate-500 mb-1">{label}</p>}
        <p className="text-sm font-bold" style={{ color: data.color || data.payload.fill || '#0f172a' }}>
          {formatter ? formatter(data.value, data.payload) : data.value}
        </p>
      </div>
    );
  }
  return null;
};


export default function Reports() {
  const { success, error } = useToast();

  const [reportData, setReportData] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [readyReports, setReadyReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState('all');
  const [exporting, setExporting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [rData, vData] = await Promise.all([
        getFleetReportData({ vehicle_id: selectedVehicle }),
        getVehicles()
      ]);
      setReportData(rData);
      setVehicles(vData);
      // Backend does not currently support fetching generated reports
      setReadyReports([]);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedVehicle]); // re-fetch when vehicle filter changes

  useEffect(() => {
    loadData();
  }, []);

  const handleExport = async (format, type) => {
    setExporting(true);
    try {
      const result = await exportReport(format, type);
      success('Report Generated', `Downloaded ${result.filename} successfully.`);
    } catch (e) {
      error('Export Failed', 'An error occurred during compilation.');
    } finally {
      setExporting(false);
    }
  };

  const columns = [
    {
      key: 'name',
      label: 'Report Name',
      render: (item) => (
        <div className="flex items-center gap-2.5">
          {item.format === 'pdf' ? (
            <FileText className="h-4 w-4 text-red-500" />
          ) : (
            <FileSpreadsheet className="h-4 w-4 text-emerald-600" />
          )}
          <span className="font-semibold text-content">{item.name}</span>
        </div>
      )
    },
    {
      key: 'type',
      label: 'Report Category'
    },
    {
      key: 'date',
      label: 'Date Compiled',
      render: (item) => <span>{new Date(item.date).toLocaleDateString()}</span>
    },
    {
      key: 'size',
      label: 'File Size'
    },
    {
      key: 'actions',
      label: 'Download',
      className: 'text-right',
      render: (item) => (
        <Button
          variant="outline"
          size="sm"
          icon={<Download className="h-4 w-4 text-brand-600" />}
          onClick={() => handleExport(item.format, item.type.toLowerCase())}
        >
          {item.format.toUpperCase()}
        </Button>
      )
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  if (err || !reportData) {
    return (
      <ErrorState
        title="Failed to Load Reports"
        message={err?.message || 'Could not fetch telemetry records.'}
        onRetry={loadData}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Reports & Analytics</h1>
          <p className="text-sm text-content-secondary mt-0.5">Generate compliance ledgers, fuel mileage trends, and safety ratings.</p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            icon={<FileText className="h-4 w-4 text-red-500" />}
            loading={exporting}
            onClick={() => handleExport('pdf', 'fleet')}
            disabled={loading || !!err}
          >
            {exporting ? 'Generating PDF...' : 'Export PDF'}
          </Button>
          <Button
            variant="outline"
            icon={<FileSpreadsheet className="h-4 w-4 text-emerald-600" />}
            loading={exporting}
            onClick={() => handleExport('csv', 'fleet')}
            disabled={loading || !!err}
          >
            {exporting ? 'Generating CSV...' : 'Export CSV'}
          </Button>
        </div>
      </div>

      {/* Customizable Filters panel */}
      <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex flex-col md:flex-row items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-content-secondary text-sm font-semibold">
            <Filter className="h-4 w-4 text-brand-600" />
            Query Bounds:
          </div>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none opacity-50 cursor-not-allowed"
              disabled
              title="Date filtering is not yet supported by the analytics engine."
            />
            <span className="text-xs text-content-muted">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none opacity-50 cursor-not-allowed"
              disabled
              title="Date filtering is not yet supported by the analytics engine."
            />
          </div>
          <div className="flex items-center gap-1 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded">
            <Info className="h-3 w-3" />
            <span>Date filters currently unsupported by API. Showing all-time data.</span>
          </div>
        </div>

        <div className="w-full md:w-auto">
          <select
            value={selectedVehicle}
            onChange={(e) => setSelectedVehicle(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none w-full md:w-48"
          >
            <option value="all">All Vehicles</option>
            {vehicles.map(v => (
              <option key={v.id} value={v.license_plate}>
                {v.license_plate}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* High-Level KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 flex items-center gap-4 border-l-4 border-brand-500">
          <div className="p-3 bg-brand-50 text-brand-600 rounded-xl">
            <Truck className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-content-secondary font-medium">Total Fleet Size</p>
            <h3 className="text-2xl font-bold text-content mt-1">{reportData.totalVehicles} <span className="text-sm font-normal text-content-muted">Vehicles</span></h3>
          </div>
        </Card>
        
        <Card className="p-4 flex items-center gap-4 border-l-4 border-blue-500">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <Route className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-content-secondary font-medium">Recorded Trips</p>
            <h3 className="text-2xl font-bold text-content mt-1">{reportData.totalTrips} <span className="text-sm font-normal text-content-muted">Trips Logged</span></h3>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-4 border-l-4 border-amber-500">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
            <IndianRupee className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-content-secondary font-medium">Total Expenditure</p>
            <h3 className="text-2xl font-bold text-content mt-1">₹{(reportData.totalExpense / 1000).toFixed(1)}k <span className="text-sm font-normal text-content-muted">YTD</span></h3>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-4 border-l-4 border-purple-500">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-content-secondary font-medium">System Health</p>
            <h3 className="text-2xl font-bold text-content mt-1">98.4% <span className="text-sm font-normal text-green-600">Optimal</span></h3>
          </div>
        </Card>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mileage line chart */}
        <Card className="space-y-4">
          <CardHeader className="p-0">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-brand-600" />
              Fuel Mileage Trends (km/L)
            </CardTitle>
          </CardHeader>
          <div className="h-72">
            {!reportData.mileageTrend || reportData.mileageTrend.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-400">No mileage data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={reportData.mileageTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} />
                  <YAxis domain={[3.5, 5.0]} stroke="#94a3b8" fontSize={11} />
                  <Tooltip content={<CustomTooltip formatter={(value) => `${value} km/L`} label="Fuel Mileage" />} />
                  <Line type="monotone" dataKey="avg_mileage" stroke="#10b981" strokeWidth={3} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        {/* Safety Score bar chart */}
        <Card className="space-y-4">
          <CardHeader className="p-0">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart2 className="h-4 w-4 text-brand-600" />
              Driver Safety Scores Audit
            </CardTitle>
          </CardHeader>
          <div className="h-72">
            {!reportData.driverSafetyStats || reportData.driverSafetyStats.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-400">No driver safety data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={reportData.driverSafetyStats} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorSafety" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.9}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.6}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} />
                  <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                  <Tooltip content={<CustomTooltip formatter={(value, payload) => `${value} / 100`} label="Driver Safety" />} />
                  <Bar dataKey="safetyScore" fill="url(#colorSafety)" radius={[4, 4, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        {/* Expense Distribution Pie Chart */}
        <Card className="space-y-4">
          <CardHeader className="p-0">
            <CardTitle className="text-base flex items-center gap-2">
              <Receipt className="h-4 w-4 text-brand-600" />
              Operational Expenses Breakdown
            </CardTitle>
          </CardHeader>
          <div className="h-72">
            {!reportData.expenseDistribution || reportData.expenseDistribution.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-400">No expense data available</div>
            ) : (
              <div className="flex flex-col lg:flex-row h-full items-center justify-center">
                <div className="w-full lg:w-3/5 h-64 lg:h-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={reportData.expenseDistribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        fill="#8884d8"
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {reportData.expenseDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        content={
                          <CustomTooltip 
                            formatter={(value, payload) => (
                              <div className="flex flex-col">
                                <span>{value}%</span>
                                {payload.payload.amount !== undefined && (
                                  <span className="text-xs font-normal text-slate-500 mt-0.5">
                                    ₹{payload.payload.amount.toLocaleString()}
                                  </span>
                                )}
                              </div>
                            )}
                          />
                        }
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="w-full lg:w-2/5 flex flex-wrap lg:flex-col justify-center gap-3 lg:gap-2 mt-4 lg:mt-0 pb-4 lg:pb-0 px-4">
                  {reportData.expenseDistribution.map((entry, index) => (
                    <div key={`legend-${index}`} className="flex items-center gap-2 text-sm">
                      <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                      <span className="text-slate-700 font-medium truncate" title={entry.name}>
                        {entry.name} <span className="text-slate-500 ml-1">{entry.value}%</span>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Vehicle Maintenance Costs Bar Chart */}
        <Card className="space-y-4">
          <CardHeader className="p-0">
            <CardTitle className="text-base flex items-center gap-2">
              <Wrench className="h-4 w-4 text-brand-600" />
              Vehicle Maintenance Costs
            </CardTitle>
          </CardHeader>
          <div className="h-72">
            {!reportData.maintenanceCostByVehicle || reportData.maintenanceCostByVehicle.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-400">No maintenance data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={reportData.maintenanceCostByVehicle} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorMaintenance" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.9}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.6}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="vehicle" stroke="#94a3b8" fontSize={10} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={(val) => `₹${val/1000}k`} />
                  <Tooltip content={<CustomTooltip formatter={(value) => `₹${value.toLocaleString()}`} />} />
                  <Bar dataKey="cost" fill="url(#colorMaintenance)" radius={[4, 4, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      {/* Compiled reports Table */}
      <Card padding="none" className="overflow-hidden">
        <CardHeader className="p-6 pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-brand-600" />
            Historical Reports
          </CardTitle>
        </CardHeader>
        {readyReports && readyReports.length > 0 ? (
          <Table
            columns={columns}
            data={readyReports}
            keyExtractor={(item) => item.id}
          />
        ) : (
          <div className="p-12 text-center flex flex-col items-center justify-center">
            <FileText className="h-12 w-12 text-slate-300 mb-4" />
            <h3 className="text-lg font-semibold text-slate-700">No reports generated yet</h3>
            <p className="text-slate-500 mt-2 max-w-sm">Generate a report using the filters above and it will appear here in your historical archives.</p>
          </div>
        )}
      </Card>
    </div>
  );
}
