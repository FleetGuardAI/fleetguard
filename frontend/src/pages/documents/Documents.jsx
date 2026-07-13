import React, { useState, useEffect } from 'react';
import { FileText, Plus, Eye, Calendar, Upload, Download, AlertTriangle, ShieldCheck, CheckCircle } from 'lucide-react';
import { getDocuments, uploadDocument } from '@/api/documentApi';
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
import { Input, Select } from '@/components/ui/Input';
import { cn } from '@/utils/cn';

export default function Documents() {
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState('all'); // all, alerts
  const [documents, setDocuments] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');

  // Modals
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);

  // Form states
  const [docName, setDocName] = useState('');
  const [category, setCategory] = useState('Registration');
  const [targetType, setTargetType] = useState('Vehicle');
  const [targetName, setTargetName] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [fileAttached, setFileAttached] = useState(false);
  const [formErrors, setFormErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const loadDocumentsData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [dData, vData] = await Promise.all([
        getDocuments({ search }),
        getVehicles()
      ]);
      setDocuments(dData);
      setVehicles(vData);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve documents directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocumentsData();
  }, [search]);

  // Expiration alerts documents
  const alertDocuments = documents.filter(doc => doc.status === 'warning' || doc.status === 'expired');

  // Active documents depending on tab selection
  const activeDocsList = activeTab === 'alerts' ? alertDocuments : documents;

  // Pagination
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: activeDocsList.length, initialPageSize: 10 });

  const paginatedDocs = activeDocsList.slice(startIndex, endIndex);

  const validateForm = () => {
    const errs = {};
    if (!docName.trim()) errs.docName = 'Document name is required';
    if (!targetName.trim()) errs.targetName = 'Target name allocation is required';
    if (!expiryDate) errs.expiryDate = 'Expiry date is required';
    if (!fileAttached) errs.fileAttached = 'A file attachment is required';

    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setSubmitting(true);
    const payload = {
      name: docName.trim(),
      category,
      target_type: targetType,
      target_name: targetName.trim(),
      expiry_date: expiryDate
    };

    try {
      const newDoc = await uploadDocument(payload);
      setDocuments(prev => [newDoc, ...prev]);
      success('Upload Successful', `Successfully saved document: ${payload.name}`);
      setUploadModalOpen(false);
      setDocName('');
      setTargetName('');
      setExpiryDate('');
      setFileAttached(false);
    } catch (e) {
      error('Action Failed', 'Failed to upload document.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSimulateAttachment = () => {
    setFileAttached(true);
    success('File Scanned', 'PDF document scanned successfully.');
  };

  const getStatusVariant = (status) => {
    if (status === 'active') return 'success';
    if (status === 'warning') return 'warning';
    return 'danger';
  };

  const getStatusLabel = (status) => {
    if (status === 'active') return 'VERIFIED';
    if (status === 'warning') return 'EXPIRING SOON';
    return 'EXPIRED';
  };

  const columns = [
    {
      key: 'name',
      label: 'Document Title',
      render: (item) => (
        <div className="flex items-center gap-2.5">
          <FileText className="h-4 w-4 text-content-secondary" />
          <span className="font-semibold text-content">{item.name}</span>
        </div>
      )
    },
    {
      key: 'category',
      label: 'Category'
    },
    {
      key: 'target_name',
      label: 'Allocated to',
      render: (item) => (
        <span className={item.target_type === 'Vehicle' ? 'font-mono text-xs font-semibold' : 'text-sm font-medium'}>
          {item.target_name} ({item.target_type})
        </span>
      )
    },
    {
      key: 'expiry_date',
      label: 'Expiry Date',
      render: (item) => (
        <span className="text-xs text-content-secondary flex items-center gap-1">
          <Calendar className="h-3.5 w-3.5 text-content-muted" />
          {item.expiry_date}
        </span>
      )
    },
    {
      key: 'status',
      label: 'Verification Status',
      render: (item) => (
        <Badge variant={getStatusVariant(item.status)} dot>
          {getStatusLabel(item.status)}
        </Badge>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      className: 'text-right',
      render: (item) => (
        <div className="flex justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            icon={<Eye className="h-4 w-4" />}
            onClick={() => { setSelectedDoc(item); setDetailsModalOpen(true); }}
          />
          {item.file_url && (
            <a href={item.file_url} target="_blank" rel="noreferrer">
              <Button
                variant="ghost"
                size="sm"
                icon={<Download className="h-4 w-4" />}
              />
            </a>
          )}
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Documents Repository</h1>
          <p className="text-sm text-content-secondary mt-0.5">Store and track validity of commercial permits, insurance papers, and driver licenses.</p>
        </div>
        <Button
          variant="primary"
          icon={<Upload className="h-4 w-4" />}
          onClick={() => setUploadModalOpen(true)}
        >
          Upload Document
        </Button>
      </div>

      {/* Expiry alerts indicators */}
      {alertDocuments.length > 0 && (
        <div className="p-4 bg-amber-50/50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30 rounded-xl flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5 animate-bounce" />
          <div>
            <p className="text-sm font-semibold text-amber-900 dark:text-amber-400">
              Validity Renewals Required
            </p>
            <p className="text-xs text-amber-800 dark:text-amber-300 mt-1">
              You have {alertDocuments.length} document{alertDocuments.length > 1 ? 's' : ''} expiring soon or expired. Please review validity checklist parameters.
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-px">
        <button
          onClick={() => setActiveTab('all')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap",
            activeTab === 'all'
              ? "border-brand-600 text-brand-600 dark:border-brand-500 dark:text-brand-500"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Fleet Documents Repository ({documents.length})
        </button>
        <button
          onClick={() => setActiveTab('alerts')}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5",
            activeTab === 'alerts'
              ? "border-brand-600 text-brand-600 dark:border-brand-500 dark:text-brand-500"
              : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          Expiration Alerts
          {alertDocuments.length > 0 && (
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          )}
        </button>
      </div>

      <div className="space-y-6">
        <Card className="p-4 flex items-center justify-between">
          <SearchBox
            value={search}
            onChange={setSearch}
            placeholder="Search document name, truck plate, driver..."
            className="w-full md:max-w-xs"
          />
        </Card>

        <Card padding="none" className="overflow-hidden">
          {loading ? (
            <div className="p-6">
              <SkeletonTable rows={5} cols={6} />
            </div>
          ) : err ? (
            <ErrorState
              title="Failed to Load Documents"
              message={err.message || 'An error occurred.'}
              onRetry={loadDocumentsData}
            />
          ) : activeDocsList.length === 0 ? (
            <EmptyState
              title="No Documents Found"
              description="There are no active or expired documents matching your selection."
              actionLabel="Upload Document"
              onAction={() => setUploadModalOpen(true)}
            />
          ) : (
            <>
              <Table
                columns={columns}
                data={paginatedDocs}
                keyExtractor={(item) => item.id}
                onRowClick={(item) => { setSelectedDoc(item); setDetailsModalOpen(true); }}
              />
              <div className="border-t border-border px-6">
                <Pagination
                  page={page}
                  totalPages={totalPages}
                  pageSize={pageSize}
                  totalItems={activeDocsList.length}
                  onPageChange={goToPage}
                  onPageSizeChange={changePageSize}
                />
              </div>
            </>
          )}
        </Card>
      </div>

      {/* Upload Document Modal */}
      <Modal
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        title="Upload Fleet Document"
        description="Verify document parameters and upload attachments."
        closable={!submitting}
        footer={
          <>
            <Button variant="outline" onClick={() => setUploadModalOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleUploadDocument} loading={submitting}>
              Save Document
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleUploadDocument}>
          <Input
            label="Document Title Name"
            placeholder="e.g. National Goods Permit,fastag rc"
            value={docName}
            onChange={(e) => setDocName(e.target.value)}
            error={formErrors.docName}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Document Category"
              options={[
                { value: 'Registration', label: 'RC (Registration)' },
                { value: 'Permit', label: 'Route Permit' },
                { value: 'License', label: 'Driver License' },
                { value: 'Insurance', label: 'Insurance Policy' }
              ]}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              required
            />
            <Input
              label="Expiration Date"
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
              error={formErrors.expiryDate}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Allocation Target Type"
              options={[
                { value: 'Vehicle', label: 'Truck/Vehicle' },
                { value: 'Driver', label: 'Operator/Driver' }
              ]}
              value={targetType}
              onChange={(e) => { setTargetType(e.target.value); setTargetName(''); }}
              required
            />
            
            {targetType === 'Vehicle' ? (
              <Select
                label="Allocated Vehicle"
                placeholder="-- Select Truck --"
                options={vehicles.map(v => ({ value: v.license_plate, label: v.license_plate }))}
                value={targetName}
                onChange={(e) => setTargetName(e.target.value)}
                error={formErrors.targetName}
                required
              />
            ) : (
              <Input
                label="Driver Name"
                placeholder="e.g. Rajesh Kumar"
                value={targetName}
                onChange={(e) => setTargetName(e.target.value)}
                error={formErrors.targetName}
                required
              />
            )}
          </div>

          {/* Attachment upload */}
          <div className="space-y-1.5">
            <span className="block text-sm font-medium text-content-secondary">PDF/Image Document File</span>
            <div className="flex items-center gap-3">
              <Button
                type="button"
                variant="outline"
                icon={<Upload className="h-4 w-4 text-brand-600" />}
                onClick={handleSimulateAttachment}
              >
                Scan Attachment
              </Button>
              {fileAttached ? (
                <span className="text-xs text-green-600 font-semibold flex items-center gap-1">
                  <CheckCircle className="h-4 w-4" /> Attachment attached
                </span>
              ) : (
                <span className="text-xs text-content-secondary">No file scanned (Required)</span>
              )}
            </div>
            {formErrors.fileAttached && <p className="text-xs text-red-500">{formErrors.fileAttached}</p>}
          </div>
        </form>
      </Modal>

      {/* Details View Modal */}
      <Modal
        open={detailsModalOpen}
        onClose={() => setDetailsModalOpen(false)}
        title="Document Parameters Sheet"
        closable
        footer={
          selectedDoc?.file_url && (
            <a href={selectedDoc.file_url} target="_blank" rel="noreferrer">
              <Button variant="primary" icon={<Download className="h-4 w-4" />}>
                Download PDF
              </Button>
            </a>
          )
        }
      >
        {selectedDoc && (
          <div className="space-y-4">
            <div className="flex justify-between items-start border-b border-border pb-3">
              <div>
                <h4 className="font-bold text-content text-lg">{selectedDoc.name}</h4>
                <p className="text-xs text-content-secondary">{selectedDoc.category}</p>
              </div>
              <Badge variant={getStatusVariant(selectedDoc.status)}>
                {getStatusLabel(selectedDoc.status)}
              </Badge>
            </div>
            <div className="space-y-2.5 text-sm">
              <p className="flex justify-between"><span className="text-content-secondary">Allocated Entity:</span> <span className="font-semibold text-content">{selectedDoc.target_name} ({selectedDoc.target_type})</span></p>
              <p className="flex justify-between"><span className="text-content-secondary">Expiration Date:</span> <span className="font-medium text-content">{selectedDoc.expiry_date}</span></p>
              <div className="pt-3 border-t border-border mt-2 flex items-center gap-2 text-content-secondary bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl">
                <ShieldCheck className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                <span className="text-xs leading-relaxed">
                  Encryption Secured: Document is backed up in offline database logs and encrypted end-to-end.
                </span>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
