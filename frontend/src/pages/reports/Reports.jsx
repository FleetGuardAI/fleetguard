import React, { useState, useEffect } from 'react';
import { FileText, Download, BarChart2, Calendar, FileSpreadsheet, DownloadCloud, TrendingUp, ShieldCheck, Filter, Wrench, Receipt, Truck, Route, IndianRupee, Activity } from 'lucide-react';
import { getFleetReportData, exportReport } from '@/api/reportApi';
import { getVehicles } from '@/api/vehicleApi';
import { getDocuments } from '@/api/documentApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';
import { useToast } from '@/components/ui/Toast';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];
import { cn } from '@/utils/cn';

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
      const [rData, vData, docsData] = await Promise.all([
        getFleetReportData(),
        getVehicles(),
        getDocuments().catch(() => [])
      ]);
      setReportData(rData);
      setVehicles(vData);

      const docs = (docsData || []).map(d => ({
        id: d.id,
        name: d.original_filename || d.filename || `Report ${d.id}`,
        type: d.category || 'Archive',
        date: d.created_at || new Date().toISOString(),
        size: d.file_size ? `${(d.file_size / (1024 * 1024)).toFixed(1)} MB` : '1.2 MB',
        format: (d.original_filename || '').endsWith('.csv') ? 'csv' : 'pdf',
      }));
      setReadyReports(docs);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve analytics.');
    } finally {
      setLoading(false);
    }
  };

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
          >
            Export PDF
          </Button>
          <Button
            variant="outline"
            icon={<FileSpreadsheet className="h-4 w-4 text-emerald-600" />}
            loading={exporting}
            onClick={() => handleExport('csv', 'fleet')}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Customizable Filters panel */}
      <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-content-secondary text-sm font-semibold">
            <Filter className="h-4 w-4 text-brand-600" />
            Query Bounds:
          </div>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
          />
          <span className="text-xs text-content-muted">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
          />
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
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={reportData.mileageTrend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} />
                <YAxis domain={[3.5, 5.0]} stroke="#94a3b8" fontSize={11} />
                <Tooltip />
                <Line type="monotone" dataKey="avg_mileage" stroke="#0f172a" strokeWidth={3} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
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
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={reportData.driverSafetyStats} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                <Tooltip />
                <Bar dataKey="safetyScore" fill="#0f62fe" radius={[4, 4, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
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
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={reportData.expenseDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {reportData.expenseDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Vehicle Maintenance Costs Area Chart */}
        <Card className="space-y-4">
          <CardHeader className="p-0">
            <CardTitle className="text-base flex items-center gap-2">
              <Wrench className="h-4 w-4 text-brand-600" />
              Vehicle Maintenance Costs
            </CardTitle>
          </CardHeader>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={reportData.maintenanceCostByVehicle} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="vehicle" stroke="#94a3b8" fontSize={10} />
                <YAxis stroke="#94a3b8" fontSize={11} tickFormatter={(val) => `₹${val/1000}k`} />
                <Tooltip formatter={(value) => `₹${value}`} />
                <Area type="monotone" dataKey="cost" stroke="#ef4444" fillOpacity={1} fill="url(#colorCost)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Compiled reports Table */}
      <Card padding="none" className="overflow-hidden">
        <CardHeader className="p-6 pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-brand-600" />
            Historical Compliance Archives
          </CardTitle>
        </CardHeader>
        <Table
          columns={columns}
          data={readyReports}
          keyExtractor={(item) => item.id}
        />
      </Card>
    </div>
  );
}
