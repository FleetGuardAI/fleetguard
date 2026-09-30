import { useState, useEffect } from 'react';
import { Search, AlertCircle, RefreshCw, KeyRound, CheckCircle, XCircle } from 'lucide-react';
import api from '../api';

interface PasswordReset {
  id: number;
  requester_type: string;
  requester_email_phone: string;
  reason: string | null;
  status: string;
  created_at: string;
}

export default function PasswordResets() {
  const [requests, setRequests] = useState<PasswordReset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const fetchRequests = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/password-resets');
      setRequests(response.data);
    } catch (err) {
      setError('Failed to load password reset requests. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleAction = async (id: number, action: 'approve' | 'reject') => {
    if (!window.confirm(`Are you sure you want to ${action} this request?`)) return;
    setActionLoading(id);
    try {
      const res = await api.post(`/password-resets/${id}/${action}`);
      setRequests(requests.map(r => r.id === id ? res.data : r));
    } catch (err) {
      alert(`Failed to ${action} request.`);
    } finally {
      setActionLoading(null);
    }
  };

  const filteredRequests = requests.filter(r => 
    r.requester_email_phone.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'PENDING': return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'APPROVED': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'REJECTED': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Password Resets</h1>
        <button onClick={fetchRequests} className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 transition shadow-sm">
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex gap-4 items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="Search by email or phone..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-500 border-t-transparent"></div>
            <p className="mt-2 text-slate-500">Loading requests...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-3" />
            <p className="text-red-600 font-medium">{error}</p>
            <button onClick={fetchRequests} className="mt-4 text-emerald-600 hover:underline">Try again</button>
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <KeyRound className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="text-lg font-medium text-slate-700">No requests found</p>
            <p>No password reset requests are currently pending.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-sm uppercase tracking-wider border-b border-slate-200">
                  <th className="px-6 py-4 font-semibold">User / Contact</th>
                  <th className="px-6 py-4 font-semibold">Type</th>
                  <th className="px-6 py-4 font-semibold">Requested At</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {filteredRequests.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-800">{req.requester_email_phone}</p>
                      {req.reason && <p className="text-slate-500 text-xs mt-1 truncate max-w-xs">{req.reason}</p>}
                    </td>
                    <td className="px-6 py-4">
                      <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded text-xs font-semibold border border-slate-200">
                        {req.requester_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                      {new Date(req.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(req.status)}`}>
                        {req.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {req.status === 'PENDING' && (
                        <div className="flex justify-end gap-2">
                          <button 
                            onClick={() => handleAction(req.id, 'approve')}
                            disabled={actionLoading === req.id}
                            className="text-emerald-600 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 rounded border border-emerald-200 font-medium transition-colors disabled:opacity-50 flex items-center gap-1"
                          >
                            <CheckCircle size={16} /> Approve
                          </button>
                          <button 
                            onClick={() => handleAction(req.id, 'reject')}
                            disabled={actionLoading === req.id}
                            className="text-red-600 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded border border-red-200 font-medium transition-colors disabled:opacity-50 flex items-center gap-1"
                          >
                            <XCircle size={16} /> Reject
                          </button>
                        </div>
                      )}
                      {req.status !== 'PENDING' && (
                         <span className="text-slate-400 text-xs italic">Processed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
