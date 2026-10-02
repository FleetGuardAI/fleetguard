import { useState, useEffect } from 'react';
import { Search, AlertCircle, RefreshCw, FileText, CheckCircle, XCircle } from 'lucide-react';
import api from '../api';

interface Document {
  id: string;
  original_filename: string;
  mime_type: string;
  status: string;
  verification_status: string;
  uploaded_by: string | null;
  company_id: number | null;
  target_type: string | null;
  target_id: string | null;
  rejection_reason: string | null;
  created_at: string;
}

export default function DocumentVerification() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [rejectingDocId, setRejectingDocId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const fetchDocuments = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/documents');
      setDocuments(response.data);
    } catch (err: any) {
      console.error("Document verification fetch failed", {
        status: err.response?.status,
        data: err.response?.data,
        url: err.config?.url
      });
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleApprove = async (id: string) => {
    if (!window.confirm("Are you sure you want to approve this document?")) return;
    setActionLoading(id);
    try {
      const res = await api.post(`/documents/${id}/approve`);
      setDocuments(documents.map(d => d.id === id ? res.data : d));
    } catch (err: any) {
      console.error("Document approve failed", {
        status: err.response?.status,
        data: err.response?.data,
        url: err.config?.url
      });
      alert("Failed to approve document.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingDocId || !rejectionReason.trim()) return;
    setActionLoading(rejectingDocId);
    try {
      const res = await api.post(`/documents/${rejectingDocId}/reject`, { reason: rejectionReason });
      setDocuments(documents.map(d => d.id === rejectingDocId ? res.data : d));
      setRejectingDocId(null);
      setRejectionReason('');
    } catch (err: any) {
      console.error("Document reject failed", {
        status: err.response?.status,
        data: err.response?.data,
        url: err.config?.url
      });
      alert("Failed to reject document.");
    } finally {
      setActionLoading(null);
    }
  };

  const filteredDocs = documents.filter(d => 
    d.original_filename.toLowerCase().includes(search.toLowerCase()) || 
    (d.target_type && d.target_type.toLowerCase().includes(search.toLowerCase()))
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
        <h1 className="text-2xl font-bold text-slate-900">Document Verification</h1>
        <button onClick={fetchDocuments} className="flex items-center gap-2 bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 transition shadow-sm">
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
              placeholder="Search documents by filename or type..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-500 border-t-transparent"></div>
            <p className="mt-2 text-slate-500">Loading documents...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-3" />
            <p className="text-red-600 font-medium">{error}</p>
            <button onClick={fetchDocuments} className="mt-4 text-emerald-600 hover:underline">Try again</button>
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <FileText className="mx-auto h-12 w-12 text-slate-300 mb-3" />
            <p className="text-lg font-medium text-slate-700">No documents found</p>
            <p>We couldn't find any documents matching your criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-sm uppercase tracking-wider border-b border-slate-200">
                  <th className="px-6 py-4 font-semibold">Document</th>
                  <th className="px-6 py-4 font-semibold">Entity Type</th>
                  <th className="px-6 py-4 font-semibold">Uploaded</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-sm">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="bg-slate-100 p-2 rounded-lg text-slate-500 border border-slate-200">
                          <FileText size={20} />
                        </div>
                        <div>
                          <p className="font-semibold text-slate-800">{doc.original_filename}</p>
                          <p className="text-slate-500 text-xs">{doc.mime_type}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-800">{doc.target_type || 'Unknown'}</p>
                      <p className="text-slate-500 text-xs font-mono">{doc.target_id}</p>
                    </td>
                    <td className="px-6 py-4 text-slate-500 whitespace-nowrap">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(doc.verification_status)}`}>
                        {doc.verification_status}
                      </span>
                      {doc.verification_status === 'REJECTED' && doc.rejection_reason && (
                        <p className="text-xs text-red-600 mt-1 max-w-xs truncate" title={doc.rejection_reason}>
                          Reason: {doc.rejection_reason}
                        </p>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {doc.verification_status === 'PENDING' && (
                        <div className="flex justify-end gap-2">
                          <button 
                            onClick={() => handleApprove(doc.id)}
                            disabled={actionLoading === doc.id}
                            className="bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200 px-3 py-1.5 rounded-lg font-medium flex items-center gap-1 transition-colors disabled:opacity-50"
                          >
                            <CheckCircle size={16} /> Approve
                          </button>
                          <button 
                            onClick={() => setRejectingDocId(doc.id)}
                            disabled={actionLoading === doc.id}
                            className="bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 px-3 py-1.5 rounded-lg font-medium flex items-center gap-1 transition-colors disabled:opacity-50"
                          >
                            <XCircle size={16} /> Reject
                          </button>
                        </div>
                      )}
                      {doc.verification_status !== 'PENDING' && (
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

      {rejectingDocId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="p-6 border-b border-slate-200">
              <h3 className="text-lg font-bold text-slate-900">Reject Document</h3>
              <p className="text-sm text-slate-500 mt-1">Please provide a reason for rejecting this document.</p>
            </div>
            <form onSubmit={handleReject} className="p-6">
              <div className="mb-4">
                <label className="block text-sm font-semibold text-slate-700 mb-2">Rejection Reason <span className="text-red-500">*</span></label>
                <textarea
                  value={rejectionReason}
                  onChange={e => setRejectionReason(e.target.value)}
                  className="w-full border border-slate-300 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  rows={4}
                  placeholder="e.g. Blurry image, mismatched details..."
                  required
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setRejectingDocId(null)} className="px-4 py-2 border border-slate-300 text-slate-700 rounded-xl hover:bg-slate-50 font-medium transition-colors">
                  Cancel
                </button>
                <button type="submit" disabled={!rejectionReason.trim() || actionLoading === rejectingDocId} className="px-4 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 font-medium flex items-center gap-2 disabled:opacity-50 transition-colors shadow-sm">
                  Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
