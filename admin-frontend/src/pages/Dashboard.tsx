import { useState, useEffect } from 'react';
import { Users, AlertCircle, CheckCircle, Clock, FileCheck } from 'lucide-react';
import api, { getApiErrorMessage } from '../api';

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [metricsRes, activityRes] = await Promise.all([
          api.get('/dashboard/metrics'),
          api.get('/dashboard/recent-activity')
        ]);
        setMetrics(metricsRes.data);
        setActivities(activityRes.data);
      } catch (err) {
        console.error("Dashboard fetch error", err);
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-lg shadow-sm">
        {error}
      </div>
    );
  }

  const stats = [
    { title: 'Open Tickets', value: metrics?.open_tickets ?? 0, icon: AlertCircle, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100' },
    { title: 'Pending Verifications', value: metrics?.pending_verifications ?? 0, icon: Clock, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-100' },
    { title: 'Tickets Resolved (Today)', value: metrics?.resolved_today ?? 0, icon: CheckCircle, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-100' },
    { title: 'Active Agents', value: metrics?.active_agents ?? 0, icon: Users, color: 'text-indigo-600', bg: 'bg-indigo-50', border: 'border-indigo-100' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Operations Dashboard</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className={`bg-white rounded-xl shadow-sm border ${stat.border} p-6 flex items-center space-x-4 transition-shadow hover:shadow-md`}>
            <div className={`p-3 rounded-xl ${stat.bg}`}>
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider">{stat.title}</p>
              <h3 className="text-3xl font-bold text-slate-800 mt-1">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50">
          <h2 className="text-lg font-bold text-slate-900">Recent Activity</h2>
        </div>
        <div className="p-6">
          {activities.length === 0 ? (
            <div className="text-center py-8">
              <FileCheck className="mx-auto h-12 w-12 text-slate-300 mb-3" />
              <p className="text-slate-500 font-medium">No recent activity found.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {activities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-4">
                  <div className="w-2 h-2 mt-2 rounded-full bg-emerald-500 flex-shrink-0"></div>
                  <div>
                    <p className="text-sm text-slate-800">
                      <span className="font-semibold">{activity.actor_name}</span> {activity.action} {activity.resource_type && <span className="font-medium text-slate-600">{activity.resource_type} ({activity.resource_id})</span>}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
