import React, { useState, useEffect } from 'react';
import { FileText, Eye, Upload, Download, Trash2, Truck, User, FileBadge, Calendar, ShieldCheck, CheckCircle } from 'lucide-react';
import { getDocuments, uploadDocument } from '@/api/documentApi';
import { getVehicles } from '@/api/vehicleApi';
import { getDrivers } from '@/api/driverApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SearchBox } from '@/components/shared/SearchBox';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';
import { Input, Select } from '@/components/ui/Input';
import { cn } from '@/utils/cn';

export default function Documents() {
  const { success, error } = useToast();

  const [activeTab, setActiveTab] = useState('vehicles'); // vehicles, drivers, permits
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [allDocs, setAllDocs] = useState([]); // This stores all simulated local documents
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const [search, setSearch] = useState('');

  // Entity Modal (Shows documents for the selected Vehicle/Driver/Company)
  const [entityModalOpen, setEntityModalOpen] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState(null);

  // Upload Modal
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [docName, setDocName] = useState('');
  const [category, setCategory] = useState('Registration');
  const [expiryDate, setExpiryDate] = useState('');
  const [fileAttached, setFileAttached] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [vData, dData, docsData] = await Promise.all([
        getVehicles().catch(() => []),
        getDrivers().catch(() => []),
        getDocuments().catch(() => [])
      ]);
      setVehicles(vData);
      setDrivers(dData);
      
      // Initialize some mock documents based on existing data if the server is empty
      const initialDocs = (docsData && docsData.length > 0) ? docsData : [
        { id: 'd1', target_id: vData[0]?.id || '1', target_type: 'vehicle', name: 'RC Book', category: 'Registration', expiry_date: '2027-10-10', file_url: '#' },
        { id: 'd2', target_id: dData[0]?.id || '1', target_type: 'driver', name: 'Driving License', category: 'License', expiry_date: '2025-05-12', file_url: '#' },
        { id: 'd3', target_id: 'company', target_type: 'permit', name: 'National Carrier Permit', category: 'Permit', expiry_date: '2026-01-01', file_url: '#' }
      ];
      setAllDocs(initialDocs);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // --- Filtering & Tab Data ---
  const getTabContent = () => {
    if (activeTab === 'vehicles') {
      let filtered = vehicles;
      if (search) filtered = filtered.filter(v => v.license_plate?.toLowerCase().includes(search.toLowerCase()));
      return filtered;
    }
    if (activeTab === 'drivers') {
      let filtered = drivers;
      if (search) filtered = filtered.filter(d => d.name?.toLowerCase().includes(search.toLowerCase()));
      return filtered;
    }
    if (activeTab === 'permits') {
      return [{ id: 'company', name: 'Company General Permits', license_plate: 'Company Level' }];
    }
    return [];
  };

  const currentData = getTabContent();

  const getEntityDocuments = (entityId, entityType) => {
    return allDocs.filter(d => String(d.target_id) === String(entityId) && d.target_type === entityType);
  };

  const handleRowClick = (item) => {
    let type = 'vehicle';
    if (activeTab === 'drivers') type = 'driver';
    if (activeTab === 'permits') type = 'permit';

    setSelectedEntity({
      ...item,
      type,
      displayName: item.name || item.license_plate || 'Entity'
    });
    setEntityModalOpen(true);
  };

  // --- Upload Logic ---
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!docName || !fileAttached) {
      error('Validation Failed', 'Please provide a document name and attach a file.');
      return;
    }
    
    setSubmitting(true);
    // Simulate upload delay
    setTimeout(() => {
      const newDoc = {
        id: `doc_${Date.now()}`,
        target_id: selectedEntity.id,
        target_type: selectedEntity.type,
        name: docName,
        category,
        expiry_date: expiryDate || 'N/A',
        file_url: '#'
      };
      setAllDocs(prev => [newDoc, ...prev]);
      success('Upload Successful', `Successfully saved document: ${docName}`);
      setUploadModalOpen(false);
      setDocName('');
      setExpiryDate('');
      setFileAttached(false);
      setSubmitting(false);
    }, 600);
  };

  const handleDeleteDoc = (docId) => {
    setAllDocs(prev => prev.filter(d => d.id !== docId));
    success('Deleted', 'Document has been removed.');
  };

  // --- Columns ---
  const mainColumns = [
    {
      key: 'name',
      label: activeTab === 'vehicles' ? 'Vehicle Number' : activeTab === 'drivers' ? 'Driver Name' : 'Entity Name',
      render: (item) => (
        <div className="flex items-center gap-2.5 cursor-pointer text-brand-600 hover:text-brand-700 font-semibold transition-colors">
          {activeTab === 'vehicles' && <Truck className="h-4 w-4" />}
          {activeTab === 'drivers' && <User className="h-4 w-4" />}
          {activeTab === 'permits' && <FileBadge className="h-4 w-4" />}
          <span>{item.name || item.license_plate}</span>
        </div>
      )
    },
    {
      key: 'docs_count',
      label: 'Attached Documents',
      render: (item) => {
        let type = 'vehicle';
        if (activeTab === 'drivers') type = 'driver';
        if (activeTab === 'permits') type = 'permit';
        const count = getEntityDocuments(item.id, type).length;
        return <Badge variant={count > 0 ? "primary" : "neutral"}>{count} Documents</Badge>;
      }
    },
    {
      key: 'actions',
      label: 'Manage',
      className: 'text-right',
      render: () => (
        <span className="text-sm font-medium text-brand-600 cursor-pointer">View / Upload →</span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content">Documents Repository</h1>
          <p className="text-sm text-content-secondary mt-0.5">Manage and track documents by Vehicles, Drivers, and Company Permits.</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border gap-2 overflow-x-auto pb-px">
        <button
          onClick={() => { setActiveTab('vehicles'); setSearch(''); }}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5",
            activeTab === 'vehicles' ? "border-brand-600 text-brand-600" : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          <Truck className="h-4 w-4" /> Vehicles
        </button>
        <button
          onClick={() => { setActiveTab('drivers'); setSearch(''); }}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5",
            activeTab === 'drivers' ? "border-brand-600 text-brand-600" : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          <User className="h-4 w-4" /> Drivers
        </button>
        <button
          onClick={() => { setActiveTab('permits'); setSearch(''); }}
          className={cn(
            "px-4 py-2 text-sm font-semibold border-b-2 transition-all whitespace-nowrap flex items-center gap-1.5",
            activeTab === 'permits' ? "border-brand-600 text-brand-600" : "border-transparent text-content-secondary hover:text-content"
          )}
        >
          <FileBadge className="h-4 w-4" /> Permits & Licenses
        </button>
      </div>

      <div className="space-y-6">
        <Card className="p-4 flex items-center justify-between">
          <SearchBox
            value={search}
            onChange={setSearch}
            placeholder={`Search ${activeTab}...`}
            className="w-full md:max-w-xs"
          />
        </Card>

        <Card padding="none" className="overflow-hidden">
          {loading ? (
            <div className="p-6">
              <SkeletonTable rows={5} cols={3} />
            </div>
          ) : err ? (
            <ErrorState
              title="Failed to Load Data"
              message={err.message || 'An error occurred.'}
              onRetry={loadData}
            />
          ) : currentData.length === 0 ? (
            <EmptyState
              title={`No ${activeTab} Found`}
              description={`There are no ${activeTab} matching your selection.`}
            />
          ) : (
            <Table
              columns={mainColumns}
              data={currentData}
              keyExtractor={(item) => item.id}
              onRowClick={handleRowClick}
            />
          )}
        </Card>
      </div>

      {/* Entity Documents Modal */}
      <Modal
        open={entityModalOpen}
        onClose={() => setEntityModalOpen(false)}
        title={selectedEntity ? `Documents for ${selectedEntity.displayName}` : 'Documents'}
        size="lg"
        footer={
          <Button variant="primary" icon={<Upload className="h-4 w-4" />} onClick={() => setUploadModalOpen(true)}>
            Upload New Document
          </Button>
        }
      >
        {selectedEntity && (
          <div className="space-y-4">
            {getEntityDocuments(selectedEntity.id, selectedEntity.type).length === 0 ? (
              <div className="p-6 text-center border border-dashed border-border rounded-xl bg-surface-tertiary">
                <FileText className="h-8 w-8 text-content-muted mx-auto mb-2" />
                <p className="text-sm text-content-secondary">No documents uploaded for this {selectedEntity.type} yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {getEntityDocuments(selectedEntity.id, selectedEntity.type).map(doc => (
                  <div key={doc.id} className="flex items-center justify-between p-4 bg-white border border-border rounded-xl hover:border-brand-200 transition-colors shadow-sm">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-brand-50 text-brand-600 rounded-lg">
                        <FileText className="h-5 w-5" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-content">{doc.name}</h4>
                        <div className="flex items-center gap-3 mt-1 text-xs text-content-secondary">
                          <span className="bg-surface-secondary px-2 py-0.5 rounded font-medium">{doc.category}</span>
                          {doc.expiry_date && doc.expiry_date !== 'N/A' && (
                            <span className="flex items-center gap-1 text-amber-600 font-medium">
                              <Calendar className="h-3 w-3" /> Expires: {doc.expiry_date}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {doc.file_url && (
                        <a href={doc.file_url} target="_blank" rel="noreferrer" title="View Document">
                          <Button variant="ghost" size="sm" icon={<Eye className="h-4 w-4 text-brand-600" />} />
                        </a>
                      )}
                      <Button variant="ghost" size="sm" className="hover:bg-red-50" icon={<Trash2 className="h-4 w-4 text-red-500" />} onClick={() => handleDeleteDoc(doc.id)} title="Delete Document" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Upload Document Modal */}
      <Modal
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        title="Upload Document"
        description={`Uploading to ${selectedEntity?.displayName}`}
        closable={!submitting}
        footer={
          <>
            <Button variant="outline" onClick={() => setUploadModalOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleUploadSubmit} loading={submitting}>
              Save Document
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleUploadSubmit}>
          <Input
            label="Document Title Name"
            placeholder="e.g. Insurance Policy 2026"
            value={docName}
            onChange={(e) => setDocName(e.target.value)}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Document Category"
              options={[
                { value: 'Registration', label: 'RC (Registration)' },
                { value: 'Permit', label: 'Route Permit' },
                { value: 'License', label: 'License' },
                { value: 'Insurance', label: 'Insurance Policy' },
                { value: 'Other', label: 'Other' }
              ]}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              required
            />
            <Input
              label="Expiration Date (Optional)"
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
            />
          </div>

          <div className="space-y-1.5 pt-2">
            <span className="block text-sm font-medium text-content-secondary">PDF/Image Document File</span>
            <div className="flex items-center gap-3">
              <Button
                type="button"
                variant="outline"
                icon={<Upload className="h-4 w-4 text-brand-600" />}
                onClick={() => { setFileAttached(true); success('File Selected', 'Document.pdf ready to upload.'); }}
              >
                Select File
              </Button>
              {fileAttached ? (
                <span className="text-xs text-green-600 font-semibold flex items-center gap-1">
                  <CheckCircle className="h-4 w-4" /> Attached
                </span>
              ) : (
                <span className="text-xs text-content-secondary">No file selected</span>
              )}
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
}
