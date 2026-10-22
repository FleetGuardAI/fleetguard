import { useState, useEffect } from 'react';
import { 
  Search, 
  AlertCircle, 
  RefreshCw, 
  KeyRound, 
  CheckCircle, 
  XCircle, 
  Copy, 
  Check, 
  Clock, 
  ShieldAlert, 
  X,
  RotateCcw,
  Info
} from 'lucide-react';
import api, { getApiErrorMessage } from '../api';

interface PasswordReset {
  id: number;
  requester_type: string;
  requester_email_phone: string;
  reason: string | null;
  status: string;
  ticket_id: number | null;
  resolved_by_id: number | null;
  user_id: number | null;
  token_issued_at: string | null;
  token_expires_at: string | null;
  token_used_at: string | null;
  token_revoked_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

interface TokenModalData {
  requestId: number;
  email: string;
  token: string;
  expiresAt: string;
  actionType: 'approved' | 'reissued';
}

export default function PasswordResets() {
  const [requests, setRequests] = useState<PasswordReset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  // Modals state
  const [tokenModal, setTokenModal] = useState<TokenModalData | null>(null);
  const [copied, setCopied] = useState(false);
  const [rejectModalReq, setRejectModalReq] = useState<PasswordReset | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [detailsModalReq, setDetailsModalReq] = useState<PasswordReset | null>(null);

  const fetchRequests = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/password-resets');
      setRequests(response.data);
    } catch (err: any) {
      console.error("Password resets fetch error", err);
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleApprove = async (req: PasswordReset) => {
    if (!window.confirm(`Approve password reset for ${req.requester_email_phone}? A unique, secure token will be generated.`)) {
      return;
    }

    setActionLoading(req.id);
    try {
      const res = await api.post(`/password-resets/${req.id}/approve`);
      // Update list
      setRequests(prev => prev.map(r => r.id === req.id ? res.data : r));
      
      // Open one-time token display modal
      if (res.data?.reset_token) {
        setTokenModal({
          requestId: req.id,
          email: req.requester_email_phone,
          token: res.data.reset_token,
          expiresAt: res.data.expires_at,
          actionType: 'approved'
        });
        setCopied(false);
      }
    } catch (err: any) {
      console.error("Approve error", err);
      alert(`Approval failed: ${getApiErrorMessage(err)}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReissue = async (req: PasswordReset) => {
    if (!window.confirm(`Reissuing will immediately invalidate any previous token for ${req.requester_email_phone} and generate a new one. Continue?`)) {
      return;
    }

    setActionLoading(req.id);
    try {
      const res = await api.post(`/password-resets/${req.id}/reissue`);
      setRequests(prev => prev.map(r => r.id === req.id ? res.data : r));

      if (res.data?.reset_token) {
        setTokenModal({
          requestId: req.id,
          email: req.requester_email_phone,
          token: res.data.reset_token,
          expiresAt: res.data.expires_at,
          actionType: 'reissued'
        });
        setCopied(false);
      }
    } catch (err: any) {
      console.error("Reissue error", err);
      alert(`Reissue failed: ${getApiErrorMessage(err)}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleOpenReject = (req: PasswordReset) => {
    setRejectModalReq(req);
    setRejectReason('');
  };

  const submitReject = async () => {
    if (!rejectModalReq) return;
    setActionLoading(rejectModalReq.id);
    try {
      const res = await api.post(`/password-resets/${rejectModalReq.id}/reject`, {
        reason: rejectReason.trim() || undefined
      });
      setRequests(prev => prev.map(r => r.id === rejectModalReq.id ? res.data : r));
      setRejectModalReq(null);
    } catch (err: any) {
      console.error("Reject error", err);
      alert(`Rejection failed: ${getApiErrorMessage(err)}`);
    } finally {
      setActionLoading(null);
    }
  };

  const copyToClipboard = () => {
    if (!tokenModal) return;
    navigator.clipboard.writeText(tokenModal.token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const filteredRequests = requests.filter(r => {
    const matchesSearch = 
      r.requester_email_phone.toLowerCase().includes(search.toLowerCase()) ||
      r.id.toString().includes(search.replace('#', '')) ||
      (r.reason && r.reason.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === 'ALL' || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const counts = {
    total: requests.length,
    pending: requests.filter(r => r.status === 'PENDING').length,
    approved: requests.filter(r => r.status === 'APPROVED').length,
    completed: requests.filter(r => r.status === 'COMPLETED').length,
    rejected: requests.filter(r => r.status === 'REJECTED').length,
  };

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'PENDING':
        return <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200"><Clock size={12} /> Pending</span>;
      case 'APPROVED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"><CheckCircle size={12} /> Approved</span>;
      case 'COMPLETED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200"><Check size={12} /> Completed</span>;
      case 'REJECTED':
        return <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200"><XCircle size={12} /> Rejected</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Password Reset Requests</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Review user reset submissions, generate secure one-time tokens, and manage authorization.
          </p>
        </div>
        <button 
          onClick={fetchRequests} 
          disabled={loading}
          className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 transition shadow-sm disabled:opacity-60 text-sm"
        >
          <RefreshCw size={16} className={loading ? "animate-spin text-emerald-600" : ""} />
          Refresh
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div 
          onClick={() => setStatusFilter('PENDING')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${statusFilter === 'PENDING' ? 'bg-amber-50/70 border-amber-300 ring-2 ring-amber-400' : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'}`}
        >
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium uppercase tracking-wider">
            <span>Awaiting Approval</span>
            <Clock size={16} className="text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{counts.pending}</p>
          <span className="text-xs text-amber-600 font-medium">Requires action</span>
        </div>

        <div 
          onClick={() => setStatusFilter('APPROVED')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${statusFilter === 'APPROVED' ? 'bg-emerald-50/70 border-emerald-300 ring-2 ring-emerald-400' : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'}`}
        >
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium uppercase tracking-wider">
            <span>Approved (Active)</span>
            <CheckCircle size={16} className="text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{counts.approved}</p>
          <span className="text-xs text-emerald-600 font-medium">Awaiting user reset</span>
        </div>

        <div 
          onClick={() => setStatusFilter('COMPLETED')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${statusFilter === 'COMPLETED' ? 'bg-blue-50/70 border-blue-300 ring-2 ring-blue-400' : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'}`}
        >
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium uppercase tracking-wider">
            <span>Completed</span>
            <Check size={16} className="text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{counts.completed}</p>
          <span className="text-xs text-blue-600 font-medium">Password updated</span>
        </div>

        <div 
          onClick={() => setStatusFilter('ALL')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${statusFilter === 'ALL' ? 'bg-slate-100 border-slate-300 ring-2 ring-slate-400' : 'bg-white border-slate-200 hover:border-slate-300 shadow-sm'}`}
        >
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium uppercase tracking-wider">
            <span>Total Requests</span>
            <KeyRound size={16} className="text-slate-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">{counts.total}</p>
          <span className="text-xs text-slate-500 font-medium">All recorded requests</span>
        </div>
      </div>

      {/* Main Content Container */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Filter and Search Bar */}
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Search by email, phone, or #ID..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white text-sm"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 text-xs font-medium">
            {['ALL', 'PENDING', 'APPROVED', 'COMPLETED', 'REJECTED'].map((filter) => (
              <button
                key={filter}
                onClick={() => setStatusFilter(filter)}
                className={`px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap ${
                  statusFilter === filter
                    ? 'bg-slate-800 text-white shadow-sm'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {filter === 'ALL' ? 'All' : filter.charAt(0) + filter.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Table Body */}
        {loading ? (
          <div className="p-16 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-500 border-t-transparent"></div>
            <p className="mt-3 text-slate-500 text-sm font-medium">Loading password reset requests...</p>
          </div>
        ) : error ? (
          <div className="p-16 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-3" />
            <p className="text-red-600 font-semibold text-base">{error}</p>
            <p className="text-slate-500 text-xs mt-1">Unable to communicate with the Super Admin API.</p>
            <button onClick={fetchRequests} className="mt-4 text-emerald-600 font-semibold hover:underline text-sm">
              Try again
            </button>
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-16 text-center text-slate-500">
            <KeyRound className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="text-base font-semibold text-slate-700">No requests found</p>
            <p className="text-xs text-slate-500 mt-1">
              {search || statusFilter !== 'ALL' 
                ? 'Try adjusting your search criteria or filter status.' 
                : 'There are currently no password reset requests submitted.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider border-b border-slate-200">
                  <th className="px-6 py-3.5 font-semibold">Request</th>
                  <th className="px-6 py-3.5 font-semibold">User / Contact</th>
                  <th className="px-6 py-3.5 font-semibold">Type</th>
                  <th className="px-6 py-3.5 font-semibold">Requested At</th>
                  <th className="px-6 py-3.5 font-semibold">Status</th>
                  <th className="px-6 py-3.5 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {filteredRequests.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-bold text-slate-600 whitespace-nowrap">
                      #{req.id}
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900">{req.requester_email_phone}</span>
                        <button 
                          onClick={() => setDetailsModalReq(req)} 
                          className="text-slate-400 hover:text-slate-600 transition"
                          title="View Request Details"
                        >
                          <Info size={14} />
                        </button>
                      </div>
                      {req.reason && (
                        <p className="text-slate-500 text-xs mt-0.5 truncate max-w-xs">{req.reason}</p>
                      )}
                      {req.rejection_reason && (
                        <p className="text-red-500 text-xs mt-0.5 truncate max-w-xs">
                          Reason: {req.rejection_reason}
                        </p>
                      )}
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-xs font-semibold border border-slate-200">
                        {req.requester_type}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-slate-500 text-xs whitespace-nowrap">
                      {new Date(req.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(req.status)}
                    </td>

                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      {req.status === 'PENDING' && (
                        <div className="flex justify-end items-center gap-2">
                          <button 
                            onClick={() => handleApprove(req)}
                            disabled={actionLoading === req.id}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg font-medium text-xs shadow-sm transition-colors disabled:opacity-50 flex items-center gap-1.5"
                          >
                            <CheckCircle size={14} /> Approve
                          </button>
                          <button 
                            onClick={() => handleOpenReject(req)}
                            disabled={actionLoading === req.id}
                            className="text-red-600 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-lg border border-red-200 font-medium text-xs transition-colors disabled:opacity-50 flex items-center gap-1.5"
                          >
                            <XCircle size={14} /> Reject
                          </button>
                        </div>
                      )}

                      {req.status === 'APPROVED' && (
                        <div className="flex justify-end items-center gap-2">
                          <button 
                            onClick={() => handleReissue(req)}
                            disabled={actionLoading === req.id}
                            className="text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-3 py-1.5 rounded-lg font-medium text-xs transition flex items-center gap-1.5"
                            title="Generate a new token if user lost the previous one"
                          >
                            <RotateCcw size={14} /> Reissue Token
                          </button>
                        </div>
                      )}

                      {req.status === 'COMPLETED' && (
                        <span className="text-slate-400 text-xs italic">
                          Completed on {req.updated_at ? new Date(req.updated_at).toLocaleDateString() : 'N/A'}
                        </span>
                      )}

                      {req.status === 'REJECTED' && (
                        <span className="text-red-400 text-xs italic">Closed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* APPROVAL & REISSUE TOKEN MODAL */}
      {tokenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden">
            {/* Modal Header */}
            <div className="bg-emerald-600 text-white p-6 flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-500/80 flex items-center justify-center">
                  <KeyRound size={22} className="text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold">
                    {tokenModal.actionType === 'reissued' ? 'New Token Reissued' : 'Reset Request Approved'}
                  </h3>
                  <p className="text-emerald-100 text-xs">
                    One-time cryptographically secure verification token
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setTokenModal(null)}
                className="text-emerald-200 hover:text-white transition p-1"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-5">
              {/* Security Warning Notice */}
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 flex gap-3 text-amber-900 text-xs leading-relaxed">
                <ShieldAlert className="text-amber-600 shrink-0 mt-0.5" size={18} />
                <div>
                  <p className="font-bold text-amber-800">Administrator Security Notice:</p>
                  <p className="mt-0.5 text-amber-700">
                    This plaintext token is returned <strong>strictly once</strong>. It is never stored in plaintext on the server and cannot be retrieved later. Copy and email it securely to the registered user.
                  </p>
                </div>
              </div>

              {/* Request Metadata */}
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-500 font-medium">User Email / Contact:</span>
                  <p className="font-bold text-slate-800 break-all mt-0.5">{tokenModal.email}</p>
                </div>
                <div>
                  <span className="text-slate-500 font-medium">Request Reference:</span>
                  <p className="font-bold text-slate-800 mt-0.5">#{tokenModal.requestId}</p>
                </div>
                <div className="col-span-2 pt-2 border-t border-slate-200 flex items-center justify-between">
                  <span className="text-slate-500 font-medium">Validity Period:</span>
                  <span className="text-emerald-700 font-semibold flex items-center gap-1">
                    <Clock size={13} />
                    Valid for 30 minutes (until {new Date(tokenModal.expiresAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                  </span>
                </div>
              </div>

              {/* Token Display Box */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Generated Reset Token
                </label>
                <div className="relative">
                  <div className="bg-slate-900 text-emerald-400 font-mono text-sm p-4 rounded-xl break-all select-all border border-slate-800">
                    {tokenModal.token}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={copyToClipboard}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all shadow-sm ${
                    copied
                      ? 'bg-emerald-700 text-white'
                      : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  }`}
                >
                  {copied ? <Check size={18} /> : <Copy size={18} />}
                  {copied ? 'Copied to Clipboard!' : 'Copy Token to Clipboard'}
                </button>
                <button
                  type="button"
                  onClick={() => setTokenModal(null)}
                  className="px-5 py-3 border border-slate-300 rounded-xl text-slate-700 font-semibold hover:bg-slate-100 transition text-sm"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* REJECT MODAL */}
      {rejectModalReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-200 p-6 space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <XCircle size={18} className="text-red-500" />
                Reject Password Reset Request
              </h3>
              <button onClick={() => setRejectModalReq(null)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Rejecting request <strong>#{rejectModalReq.id}</strong> for <strong>{rejectModalReq.requester_email_phone}</strong>.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Rejection Reason (Optional, visible to user notification)
              </label>
              <textarea
                value={rejectReason}
                onChange={e => setRejectReason(e.target.value)}
                placeholder="e.g. Account not verified or requested via unrecognized channel"
                rows={3}
                className="w-full text-xs p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setRejectModalReq(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 rounded-lg border border-slate-200"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitReject}
                disabled={actionLoading === rejectModalReq.id}
                className="px-4 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm disabled:opacity-50"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DETAILS MODAL */}
      {detailsModalReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 p-6 space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-200">
              <h3 className="text-base font-bold text-slate-900">
                Request Details — #{detailsModalReq.id}
              </h3>
              <button onClick={() => setDetailsModalReq(null)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Contact / Email:</span>
                <span className="font-semibold text-slate-800">{detailsModalReq.requester_email_phone}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Account Type:</span>
                <span className="font-semibold text-slate-800">{detailsModalReq.requester_type}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Current Status:</span>
                <span>{getStatusBadge(detailsModalReq.status)}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Submitted At:</span>
                <span className="font-semibold text-slate-800">{new Date(detailsModalReq.created_at).toLocaleString()}</span>
              </div>
              {detailsModalReq.token_issued_at && (
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Token Issued At:</span>
                  <span className="font-semibold text-slate-800">{new Date(detailsModalReq.token_issued_at).toLocaleString()}</span>
                </div>
              )}
              {detailsModalReq.token_expires_at && (
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Token Expiry:</span>
                  <span className="font-semibold text-slate-800">{new Date(detailsModalReq.token_expires_at).toLocaleString()}</span>
                </div>
              )}
              {detailsModalReq.token_used_at && (
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Token Used At:</span>
                  <span className="font-semibold text-blue-700">{new Date(detailsModalReq.token_used_at).toLocaleString()}</span>
                </div>
              )}
              {detailsModalReq.token_revoked_at && (
                <div className="flex justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Token Revoked At:</span>
                  <span className="font-semibold text-red-600">{new Date(detailsModalReq.token_revoked_at).toLocaleString()}</span>
                </div>
              )}
              {detailsModalReq.rejection_reason && (
                <div className="py-1.5">
                  <span className="text-slate-500 block mb-1">Rejection Reason:</span>
                  <p className="bg-red-50 text-red-700 p-2.5 rounded-lg border border-red-200">
                    {detailsModalReq.rejection_reason}
                  </p>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-3">
              <button
                type="button"
                onClick={() => setDetailsModalReq(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
