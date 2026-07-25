import React, { useState, useEffect } from 'react';
import { CreditCard, Plus, Eye, CheckCircle, Search, Compass, FileText, Check, DollarSign } from 'lucide-react';
import { getPayments, recordPayout } from '@/api/paymentApi';
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
import { Input, Select } from '@/components/ui/Input';
import { cn } from '@/utils/cn';

export default function Payments() {
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState('transactions'); // transactions, vendors
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');

  // Modals
  const [newPayoutModalOpen, setNewPayoutModalOpen] = useState(false);
  const [payoutDetailsModalOpen, setPayoutDetailsModalOpen] = useState(false);
  const [selectedPayout, setSelectedPayout] = useState(null);

  // Form states
  const [recipientName, setRecipientName] = useState('');
  const [payoutType, setPayoutType] = useState('Vendor Payout');
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState('UPI');
  const [description, setDescription] = useState('');
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const [vendors, setVendors] = useState([]);

  const loadPayments = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getPayments({ search });
      setPayments(data);

      const uniqueVendors = Array.from(
        new Set(data.map(p => p.recipient_name).filter(Boolean))
      ).map((vName, idx) => ({
        id: idx + 1,
        name: vName,
        type: 'Registered Vendor',
        contact: 'N/A',
        upi: `${vName.toLowerCase().replace(/[^a-z0-9]/g, '')}@okbiz`,
        status: 'verified'
      }));
      setVendors(uniqueVendors);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve transactions list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, [search]);

  // Pagination
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: payments.length, initialPageSize: 10 });

  const paginatedPayments = payments.slice(startIndex, endIndex);

  const validateForm = () => {
    const errs = {};
    if (!recipientName.trim()) errs.recipientName = 'Recipient name is required';
    if (!amount) {
      errs.amount = 'Payout cost amount is required';
    } else if (Number(amount) <= 0) {
      errs.amount = 'Cost must be positive';
    }
    if (!description.trim()) errs.description = 'Payout description is required';

    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleCreatePayout = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setSubmitting(true);
    const payload = {
      recipient_name: recipientName.trim(),
      type: payoutType,
      amount: Number(amount),
      method,
      description: description.trim()
    };

    try {
      const newPay = await recordPayout(payload);
      setPayments(prev => [newPay, ...prev]);
      success('Payout Logged', `Successfully recorded transaction ${newPay.id}.`);
      setNewPayoutModalOpen(false);
      setRecipientName('');
      setAmount('');
      setDescription('');
    } catch (e) {
      error('Action Failed', 'Failed to submit transaction.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewPayout = (payout) => {
    setSelectedPayout(payout);
    setPayoutDetailsModalOpen(true);
  };

  const handleSettlePayout = async (id) => {
    // Mock settle
    setPayments(prev => prev.map(p => p.id === id ? { ...p, status: 'completed', ref_num: 'TXN-' + Math.floor(1000000000 + Math.random() * 9000000000) } : p));
    success('Payout Settled', 'Transaction successfully completed.');
    setPayoutDetailsModalOpen(false);
  };

  const columns = [
    {
      key: 'id',
      label: 'TXN ID',
      render: (item) => <span className="font-semibold text-content">{item.id}</span>
    },
    {
      key: 'recipient_name',
      label: 'Recipient',
      render: (item) => <span className="font-medium text-content">{item.recipient_name}</span>
    },
    {
      key: 'type',
      label: 'Type'
    },
    {
      key: 'amount',
      label: 'Cost Amount',
      render: (item) => <span className="font-bold">₹{item.amount.toLocaleString()}</span>
    },
    {
      key: 'method',
      label: 'Method',
      render: (item) => <span className="text-xs px-2 py-0.5 bg-slate-100 rounded text-slate-700 font-mono">{item.method}</span>
    },
    {
      key: 'date',
      label: 'Timestamp',
      render: (item) => <span>{new Date(item.date).toLocaleDateString()}</span>
    },
    {
      key: 'status',
      label: 'Status',
      render: (item) => (
        <Badge variant={item.status === 'completed' ? 'success' : 'warning'} dot>
          {item.status.toUpperCase()}
        </Badge>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (item) => (
        <div className="flex justify-end">
          <Button
            variant="ghost"
            size="sm"
            icon={<Eye className="h-4 w-4" />}
            onClick={() => handleViewPayout(item)}
          />
        </div>
      )
    }
  ];

  const vendorColumns = [
    { key: 'name', label: 'Vendor Name', render: (item) => <span className="font-semibold">{item.name}</span> },
    { key: 'type', label: 'Service Category' },
    { key: 'contact', label: 'Contact Phone' },
    { key: 'upi', label: 'UPI Address Account', render: (item) => <span className="font-mono text-xs">{item.upi}</span> },
    { key: 'status', label: 'KYC Status', render: (item) => <Badge variant="success">VERIFIED</Badge> }
  ];

  const totalCompleted = payments.filter(p => p.status === 'completed').reduce((sum, p) => sum + p.amount, 0);
  const totalPending = payments.filter(p => p.status === 'pending').reduce((sum, p) => sum + p.amount, 0);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Payments & Settlements</h1>
          <p className="text-sm text-content-secondary mt-0.5">Disburse advances to drivers and clear pending payouts to vendors.</p>
        </div>
        <Button
          variant="primary"
          icon={<Plus className="h-4 w-4" />}
          onClick={() => setNewPayoutModalOpen(true)}
        >
          New Payout
        </Button>
      </div>

      {/* Stats Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-secondary uppercase">Disbursed Settlements (Today)</span>
          <h3 className="text-2xl font-extrabold text-content mt-2">₹{totalCompleted.toLocaleString()}</h3>
        </Card>
        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-secondary uppercase">Pending Approvals</span>
          <h3 className="text-2xl font-extrabold text-content mt-2">₹{totalPending.toLocaleString()}</h3>
        </Card>
        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-secondary uppercase">Active Vendors</span>
          <h3 className="text-2xl font-extrabold text-content mt-2">{vendors.length} Verified</h3>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-px">
        <button
          onClick={() => setActiveTab('transactions')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            activeTab === 'transactions'
              ? "border-brand-600 text-brand-600 dark:border-brand-500 dark:text-brand-500"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Settlements & Transactions
        </button>
        <button
          onClick={() => setActiveTab('vendors')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            activeTab === 'vendors'
              ? "border-brand-600 text-brand-600 dark:border-brand-500 dark:text-brand-500"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Vendor Directory
        </button>
      </div>

      {activeTab === 'transactions' ? (
        <div className="space-y-6">
          <Card className="p-4 flex items-center justify-between">
            <SearchBox
              value={search}
              onChange={setSearch}
              placeholder="Search recipient, transaction ID..."
              className="w-full md:max-w-xs"
            />
          </Card>

          <Card padding="none" className="overflow-hidden">
            {loading ? (
              <div className="p-6">
                <SkeletonTable rows={5} cols={8} />
              </div>
            ) : err ? (
              <ErrorState
                title="Failed to Load Transactions"
                message={err.message || 'An error occurred.'}
                onRetry={loadPayments}
              />
            ) : payments.length === 0 ? (
              <EmptyState
                title="No Transactions Logged"
                description="There are no payment settlements matching your criteria."
                actionLabel="Create Payout"
                onAction={() => setNewPayoutModalOpen(true)}
              />
            ) : (
              <>
                <Table
                  columns={columns}
                  data={paginatedPayments}
                  keyExtractor={(item) => item.id}
                  onRowClick={(item) => handleViewPayout(item)}
                />
                <div className="border-t border-border px-6">
                  <Pagination
                    page={page}
                    totalPages={totalPages}
                    pageSize={pageSize}
                    totalItems={payments.length}
                    onPageChange={goToPage}
                    onPageSizeChange={changePageSize}
                  />
                </div>
              </>
            )}
          </Card>
        </div>
      ) : (
        <Card padding="none" className="overflow-hidden">
          <Table
            columns={vendorColumns}
            data={vendors}
            keyExtractor={(item) => item.id}
          />
        </Card>
      )}

      {/* New Payout Modal */}
      <Modal
        open={newPayoutModalOpen}
        onClose={() => setNewPayoutModalOpen(false)}
        title="Record New Payout"
        description="Allocate financial settlements or Fastag advances."
        closable={!submitting}
        footer={
          <>
            <Button variant="outline" onClick={() => setNewPayoutModalOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleCreatePayout} loading={submitting}>
              Confirm Payout
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleCreatePayout}>
          <Input
            label="Recipient Name"
            placeholder="e.g. Sharma Tyre Works, Rajesh Kumar"
            value={recipientName}
            onChange={(e) => setRecipientName(e.target.value)}
            error={formErrors.recipientName}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Payout Type"
              options={[
                { value: 'Vendor Payout', label: 'Vendor Settlement' },
                { value: 'Fuel Card Recharge', label: 'Fuel Card Top-Up' },
                { value: 'Driver Advance', label: 'Driver advance' },
                { value: 'Fastag Recharge', label: 'Fastag Toll Top-Up' }
              ]}
              value={payoutType}
              onChange={(e) => setPayoutType(e.target.value)}
              required
            />
            <Input
              label="Payout Cost (INR)"
              type="number"
              min="1"
              placeholder="e.g. 5000"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              error={formErrors.amount}
              required
            />
          </div>

          <Select
            label="Settlement Method"
            options={[
              { value: 'UPI', label: 'BHIM UPI' },
              { value: 'NetBanking', label: 'Corporate NetBanking' },
              { value: 'IMPS', label: 'IMPS Bank Transfer' }
            ]}
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            required
          />

          <Input
            label="Description / Purpose Notes"
            placeholder="e.g. Cleared puncture repairs bill from 12th July"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            error={formErrors.description}
            required
          />
        </form>
      </Modal>

      {/* Payout Details / Verification Modal */}
      <Modal
        open={payoutDetailsModalOpen}
        onClose={() => setPayoutDetailsModalOpen(false)}
        title={`Payout Verification`}
        closable
        footer={
          selectedPayout?.status === 'pending' && (
            <Button
              variant="primary"
              icon={<Check className="h-4 w-4" />}
              onClick={() => handleSettlePayout(selectedPayout.id)}
            >
              Mark Settled
            </Button>
          )
        }
      >
        {selectedPayout && (
          <div className="space-y-4">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h4 className="font-bold text-content text-lg">{selectedPayout.recipient_name}</h4>
                <p className="text-xs text-content-secondary">{selectedPayout.type}</p>
              </div>
              <Badge variant={selectedPayout.status === 'completed' ? 'success' : 'warning'}>
                {selectedPayout.status.toUpperCase()}
              </Badge>
            </div>
            <div className="space-y-2.5 text-sm">
              <p className="flex justify-between"><span className="text-content-secondary">Amount:</span> <span className="font-bold text-brand-600">₹{selectedPayout.amount.toLocaleString()}</span></p>
              <p className="flex justify-between"><span className="text-content-secondary">Method:</span> <span className="font-medium">{selectedPayout.method}</span></p>
              <p className="flex justify-between"><span className="text-content-secondary">Date recorded:</span> <span className="font-medium">{new Date(selectedPayout.date).toLocaleString()}</span></p>
              {selectedPayout.ref_num && (
                <p className="flex justify-between"><span className="text-content-secondary">Reference ID:</span> <span className="font-mono text-xs text-content">{selectedPayout.ref_num}</span></p>
              )}
              <div className="pt-2 border-t border-border mt-2">
                <span className="text-xs text-content-secondary block uppercase font-semibold">Purpose Description</span>
                <p className="text-xs text-content mt-1 italic">{selectedPayout.description}</p>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
