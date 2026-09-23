import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Eye, Check, X, ShieldAlert, Award, FileText, AlertTriangle, PieChart as PieIcon } from 'lucide-react';
import { getExpenses, approveExpense, rejectExpense } from '@/api/expenseApi';
import { getVehicles } from '@/api/vehicleApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SearchBox } from '@/components/shared/SearchBox';
import { Pagination } from '@/components/ui/Pagination';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { useToast } from '@/components/ui/Toast';
import { usePagination } from '@/hooks/usePagination';
import { Modal } from '@/components/ui/Modal';
import { cn } from '@/utils/cn';

export default function ExpenseDashboard() {
  const navigate = useNavigate();
  const { success, error, info } = useToast();

  const [activeTab, setActiveTab] = useState('claims'); // claims, analytics
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  // Receipt Modal State
  const [receiptModalOpen, setReceiptModalOpen] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Rejection Reason Dialog State
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [rejectTargetId, setRejectTargetId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const loadExpenses = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getExpenses({
        search,
        category: categoryFilter,
        status: statusFilter
      });
      setExpenses(data);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve expense claims.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExpenses();
  }, [search, categoryFilter, statusFilter]);

  // Pagination
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: expenses.length, initialPageSize: 10 });

  const paginatedExpenses = expenses.slice(startIndex, endIndex);

  const handleApprove = async (id) => {
    setActionLoading(true);
    try {
      const updated = await approveExpense(id);
      setExpenses(prev => prev.map(e => e.id === id ? updated : e));
      success('Claim Approved', `Approved expense claim #${id} successfully.`);
      if (selectedExpense && selectedExpense.id === id) {
        setSelectedExpense(updated);
      }
    } catch (e) {
      error('Action Failed', e.message || 'Failed to approve claim.');
    } finally {
      setActionLoading(false);
    }
  };

  const openRejectDialog = (id) => {
    setRejectTargetId(id);
    setRejectionReason('');
    setRejectModalOpen(true);
  };

  const handleConfirmReject = async () => {
    if (!rejectionReason.trim()) {
      error('Rejection Reason Required', 'Please provide a reason for rejecting this expense claim.');
      return;
    }
    setActionLoading(true);
    try {
      const updated = await rejectExpense(rejectTargetId, rejectionReason.trim());
      setExpenses(prev => prev.map(e => e.id === rejectTargetId ? updated : e));
      info('Claim Rejected', `Rejected expense claim #${rejectTargetId}.`);
      if (selectedExpense && selectedExpense.id === rejectTargetId) {
        setSelectedExpense(updated);
      }
      setRejectModalOpen(false);
      setRejectTargetId(null);
      setRejectionReason('');
    } catch (e) {
      error('Action Failed', e.message || 'Failed to reject claim.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleViewReceipt = (expense) => {
    setSelectedExpense(expense);
    setReceiptModalOpen(true);
  };

  const getRiskColor = (risk) => {
    if (risk === 'High' || risk === 'Critical') return 'danger';
    if (risk === 'Medium') return 'warning';
    return 'success';
  };

  const getCategoryLabel = (cat) => {
    const map = { repair: 'Repair', fuel: 'Fuel Filling', toll: 'Toll Charge', fine: 'Fine / Penalty', other: 'Other' };
    return map[cat] || cat;
  };

  const columns = [
    {
      key: 'id',
      label: 'Claim ID',
      render: (item) => <span className="font-semibold text-content">#{item.id}</span>
    },
    {
      key: 'truck_plate',
      label: 'Vehicle Plate',
      render: (item) => <span className="font-mono text-xs font-semibold">{item.truck_plate}</span>
    },
    {
      key: 'category',
      label: 'Category',
      render: (item) => <span>{getCategoryLabel(item.category)}</span>
    },
    {
      key: 'title',
      label: 'Title / Description',
      render: (item) => <span className="truncate max-w-[150px] block">{item.title}</span>
    },
    {
      key: 'amount',
      label: 'Cost Amount',
      render: (item) => <span className="font-bold">₹{item.amount.toLocaleString()}</span>
    },
    {
      key: 'ai_risk',
      label: 'AI Verification',
      render: (item) => (
        <Badge variant={getRiskColor(item.ai_risk)}>
          {item.ai_risk} Risk
        </Badge>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (item) => {
        const s = (item.status || '').toUpperCase();
        return (
          <div className="flex items-center gap-1.5">
            <Badge variant={s === 'APPROVED' ? 'success' : s === 'REJECTED' ? 'danger' : 'warning'} dot>
              {s}
            </Badge>
            {s === 'REJECTED' && item.rejection_reason && (
              <span className="text-[10px] text-red-500 max-w-[120px] truncate" title={item.rejection_reason}>
                {item.rejection_reason}
              </span>
            )}
          </div>
        );
      }
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (item) => {
        const s = (item.status || '').toUpperCase();
        return (
          <div className="flex justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="sm"
              icon={<Eye className="h-4 w-4" />}
              onClick={() => handleViewReceipt(item)}
              title="Receipt & AI details"
            />
            {s === 'PENDING' && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-green-600 hover:bg-green-50"
                  icon={<Check className="h-4 w-4" />}
                  onClick={() => handleApprove(item.id)}
                  disabled={actionLoading}
                  title="Approve"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-500 hover:bg-red-50"
                  icon={<X className="h-4 w-4" />}
                  onClick={() => openRejectDialog(item.id)}
                  disabled={actionLoading}
                  title="Reject"
                />
              </>
            )}
          </div>
        );
      }
    }
  ];

  // Aggregated analytics values
  const totalFuel = expenses.filter(e => e.category === 'fuel').reduce((sum, e) => sum + e.amount, 0);
  const totalRepairs = expenses.filter(e => e.category === 'repair').reduce((sum, e) => sum + e.amount, 0);
  const totalToll = expenses.filter(e => e.category === 'toll').reduce((sum, e) => sum + e.amount, 0);
  const totalOther = expenses.filter(e => e.category !== 'fuel' && e.category !== 'repair' && e.category !== 'toll').reduce((sum, e) => sum + e.amount, 0);
  const grandTotal = totalFuel + totalRepairs + totalToll + totalOther;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Expense Management</h1>
          <p className="text-sm text-content-secondary mt-0.5">Audit driver expense logs, OCR verified receipts, and check pricing anomalies.</p>
        </div>
        <Button
          variant="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => navigate('/dashboard/expenses/new')}
        >
          Add Expense
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-px">
        <button
          onClick={() => setActiveTab('claims')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            activeTab === 'claims'
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Expense Claims Directory
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            activeTab === 'analytics'
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Expense Category Analytics
        </button>
      </div>

      {activeTab === 'claims' ? (
        <div className="space-y-6">
          {/* Filters Toolbar */}
          <Card className="p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
            <SearchBox
              value={search}
              onChange={setSearch}
              placeholder="Search truck, driver, claim description..."
              className="w-full md:max-w-xs"
            />
            <div className="flex flex-wrap gap-2 w-full md:w-auto">
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
              >
                <option value="all">All Categories</option>
                <option value="repair">Repairs</option>
                <option value="fuel">Fuel Fills</option>
                <option value="toll">Tolls</option>
                <option value="fine">Fines</option>
                <option value="other">Others</option>
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none"
              >
                <option value="all">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </Card>

          {/* Claims Table */}
          <Card padding="none" className="overflow-hidden">
            {loading ? (
              <div className="p-6">
                <SkeletonTable rows={5} cols={8} />
              </div>
            ) : err ? (
              <ErrorState
                title="Failed to Load Expenses"
                message={err.message || 'An error occurred.'}
                onRetry={loadExpenses}
              />
            ) : expenses.length === 0 ? (
              <EmptyState
                title="No Expense Claims logged"
                description="There are no tickets matching the current filtering criteria."
                actionLabel="Create Claim"
                onAction={() => navigate('/dashboard/expenses/new')}
              />
            ) : (
              <>
                <Table
                  columns={columns}
                  data={paginatedExpenses}
                  keyExtractor={(item) => item.id}
                  onRowClick={(item) => handleViewReceipt(item)}
                />
                <div className="border-t border-border px-6">
                  <Pagination
                    page={page}
                    totalPages={totalPages}
                    pageSize={pageSize}
                    totalItems={expenses.length}
                    onPageChange={goToPage}
                    onPageSizeChange={changePageSize}
                  />
                </div>
              </>
            )}
          </Card>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Visual categories indicators */}
            <Card className="lg:col-span-2 space-y-6">
              <CardHeader className="p-0">
                <CardTitle className="text-base flex items-center gap-2">
                  <PieIcon className="h-4 w-4 text-brand-600" />
                  Category Distributions Breakdown
                </CardTitle>
              </CardHeader>
              <div className="space-y-4">
                {[
                  { label: 'Fuel Fills', amount: totalFuel, color: 'bg-emerald-500' },
                  { label: 'Repairs & Maintenance', amount: totalRepairs, color: 'bg-blue-500' },
                  { label: 'Tolls & Fastag', amount: totalToll, color: 'bg-purple-500' },
                  { label: 'Fines / Other Costs', amount: totalOther, color: 'bg-amber-500' }
                ].map((item, idx) => {
                  const percentage = grandTotal > 0 ? (item.amount / grandTotal) * 100 : 0;
                  return (
                    <div key={idx} className="space-y-1.5 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="font-semibold text-content">{item.label}</span>
                        <span className="text-content-secondary">₹{item.amount.toLocaleString()} ({percentage.toFixed(1)}%)</span>
                      </div>
                      <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                        <div className={cn("h-full transition-all duration-300", item.color)} style={{ width: `${percentage}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card className="lg:col-span-1 flex flex-col justify-between">
              <CardHeader className="p-0">
                <CardTitle className="text-base text-content-secondary uppercase">Operational Expenses Total</CardTitle>
              </CardHeader>
              <div className="py-6">
                <h3 className="text-3xl font-extrabold text-content">₹{grandTotal.toLocaleString()}</h3>
                <p className="text-xs text-content-secondary mt-1">Aggregated values of filters matched claims</p>
              </div>
              <div className="p-3 bg-brand-50/50 border border-brand-100 rounded-xl">
                <p className="text-xs text-brand-900 leading-relaxed">
                  OCR visual receipt check scans for vendor duplication, pricing benchmarks and location correlations in real time.
                </p>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Receipt Viewer & AI Details Modal */}
      <Modal
        open={receiptModalOpen}
        onClose={() => setReceiptModalOpen(false)}
        title={`Expense Claim Verification #${selectedExpense?.id}`}
        description="Verify document OCR and safety parameters."
        closable
        footer={
          selectedExpense && (selectedExpense.status || '').toUpperCase() === 'PENDING' && (
            <>
              <Button
                variant="outline"
                className="text-red-500 border-red-200 hover:bg-red-50"
                onClick={() => openRejectDialog(selectedExpense.id)}
                disabled={actionLoading}
              >
                Reject Claim
              </Button>
              <Button
                variant="primary"
                onClick={() => handleApprove(selectedExpense.id)}
                loading={actionLoading}
              >
                Approve & Pay
              </Button>
            </>
          )
        }
      >
        {selectedExpense && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Visual Receipt */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-content-secondary block uppercase">Uploaded Receipt Slip</span>
              {selectedExpense.receipt_url || selectedExpense.receiptUrl ? (
                <div className="border border-border rounded-xl overflow-hidden shadow-sm aspect-[3/4] bg-slate-50 flex items-center justify-center">
                  <img src={selectedExpense.receipt_url || selectedExpense.receiptUrl} alt="Expense Slip" className="w-full h-full object-cover" />
                </div>
              ) : (
                <div className="border border-dashed border-border rounded-xl aspect-[3/4] bg-slate-50 flex flex-col items-center justify-center text-center p-4 text-content-secondary">
                  <FileText className="h-10 w-10 text-content-muted mb-2" />
                  <span className="text-xs font-semibold">No Receipt Attachment</span>
                  <span className="text-[10px] text-content-muted mt-0.5">Driver did not upload a receipt photo.</span>
                </div>
              )}
            </div>

            {/* Audit Details */}
            <div className="space-y-4">
              <div className="space-y-2">
                <span className="text-xs font-bold text-content-secondary block uppercase">Claim Metadata</span>
                <div className="text-sm space-y-1.5">
                  <p><span className="text-content-secondary">Driver:</span> <span className="font-semibold text-content">{selectedExpense.driver_name || 'N/A'}</span></p>
                  <p><span className="text-content-secondary">Date:</span> <span className="font-medium text-content">{selectedExpense.date ? new Date(selectedExpense.date).toLocaleDateString() : 'N/A'}</span></p>
                  <p><span className="text-content-secondary">Category:</span> <span className="font-medium text-content">{getCategoryLabel(selectedExpense.category)}</span></p>
                  <p><span className="text-content-secondary">Claim Cost:</span> <span className="font-bold text-brand-600 text-lg">₹{(selectedExpense.amount || 0).toLocaleString()}</span></p>
                </div>
              </div>

              {/* Reviewer Info — shown for APPROVED/REJECTED */}
              {selectedExpense.reviewed_by && (
                <div className={cn(
                  "p-3 rounded-xl border space-y-1",
                  (selectedExpense.status || '').toUpperCase() === 'APPROVED'
                    ? "bg-emerald-50/50 border-emerald-100"
                    : "bg-red-50/50 border-red-100"
                )}>
                  <span className="text-xs font-bold text-content-secondary block uppercase">Review Decision</span>
                  <p className="text-sm">
                    <span className="text-content-secondary">Reviewed by:</span>{' '}
                    <span className="font-semibold">User #{selectedExpense.reviewed_by}</span>
                  </p>
                  {selectedExpense.reviewed_at && (
                    <p className="text-xs text-content-secondary">
                      on {new Date(selectedExpense.reviewed_at).toLocaleString()}
                    </p>
                  )}
                  {selectedExpense.rejection_reason && (
                    <div className="mt-2 p-2 bg-red-50 rounded-lg border border-red-100">
                      <span className="text-xs font-bold text-red-700 block">Rejection Reason:</span>
                      <p className="text-sm text-red-900 mt-0.5">{selectedExpense.rejection_reason}</p>
                    </div>
                  )}
                </div>
              )}

              {/* AI check card */}
              {selectedExpense.ai_risk && (
                <div className={cn(
                  "p-4 rounded-xl border space-y-2",
                  selectedExpense.ai_risk === 'Critical' && (selectedExpense.ai_details || '').toUpperCase().includes('GEOGRAPHIC FRAUD')
                    ? "bg-red-600 border-red-700 text-white shadow-lg animate-pulse"
                    : selectedExpense.ai_risk === 'High' || selectedExpense.ai_risk === 'Critical'
                      ? "bg-red-50/50 border-red-100 text-red-950"
                      : "bg-emerald-50/50 border-emerald-100 text-emerald-950"
                )}>
                  <div className="flex items-center gap-2">
                    {selectedExpense.ai_risk === 'High' || selectedExpense.ai_risk === 'Critical' ? (
                      <AlertTriangle className={cn("h-5 w-5 flex-shrink-0", selectedExpense.ai_risk === 'Critical' && (selectedExpense.ai_details || '').toUpperCase().includes('GEOGRAPHIC FRAUD') ? "text-white" : "text-red-600")} />
                    ) : (
                      <Award className="h-5 w-5 text-emerald-600 flex-shrink-0" />
                    )}
                    <span className="text-sm font-bold">
                      {selectedExpense.ai_risk === 'Critical' && (selectedExpense.ai_details || '').toUpperCase().includes('GEOGRAPHIC FRAUD') 
                        ? 'CRITICAL ALERT: GEOGRAPHIC FRAUD DETECTED' 
                        : `AI OCR Risk: ${selectedExpense.ai_risk}`}
                    </span>
                  </div>
                  <p className={cn("text-xs leading-relaxed opacity-90", selectedExpense.ai_risk === 'Critical' && (selectedExpense.ai_details || '').toUpperCase().includes('GEOGRAPHIC FRAUD') ? "font-medium" : "")}>
                    {selectedExpense.ai_details}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Rejection Reason Dialog */}
      <Modal
        open={rejectModalOpen}
        onClose={() => { setRejectModalOpen(false); setRejectTargetId(null); setRejectionReason(''); }}
        title="Reject Expense Claim"
        description="Please provide a reason for rejecting this expense claim. This will be recorded and visible to the driver."
        closable
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => { setRejectModalOpen(false); setRejectTargetId(null); setRejectionReason(''); }}
              disabled={actionLoading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              className="bg-red-600 hover:bg-red-700"
              onClick={handleConfirmReject}
              loading={actionLoading}
              disabled={!rejectionReason.trim()}
            >
              Confirm Rejection
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <label className="block text-sm font-semibold text-content">Rejection Reason *</label>
          <textarea
            className="w-full h-24 p-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
            placeholder="e.g. Receipt amount does not match claim, duplicate submission, insufficient documentation..."
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            maxLength={1000}
          />
          <p className="text-xs text-content-secondary">{rejectionReason.length}/1000 characters</p>
        </div>
      </Modal>
    </div>
  );
}
