import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Edit2, Trash2, Phone, Star, ShieldAlert, Truck, FileText, Upload, Calendar, RefreshCw, CheckCircle, Clock, AlertTriangle, User, XCircle } from 'lucide-react';
import { getDriverById, assignVehicle, getDriverDocuments, verifyDriverDocument, approveDriver } from '@/api/driverApi';
import { getVehicles } from '@/api/vehicleApi';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';

export default function DriverProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [driver, setDriver] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Assign vehicle state
  const [vehicles, setVehicles] = useState([]);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [selectedVehicleId, setSelectedVehicleId] = useState('');
  const [assigning, setAssigning] = useState(false);

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [documents, setDocuments] = useState([]);
  const [verifyingDoc, setVerifyingDoc] = useState(null);
  const [verifyStatus, setVerifyStatus] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');

  // Driver approval state
  const [approving, setApproving] = useState(false);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [driverRejectionReason, setDriverRejectionReason] = useState('');

  const loadData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const [d, v, docsData] = await Promise.all([
        getDriverById(id),
        getVehicles(),
        getDriverDocuments(id).catch(() => [])
      ]);
      setDriver(d);
      setVehicles(v);

      const mappedDocs = (docsData || []).map(doc => ({
        id: doc.id,
        name: doc.category ? doc.category.replace('_', ' ').toUpperCase() : `Document #${doc.id}`,
        category: doc.category,
        status: doc.verification_status.toLowerCase(),
        url: doc.storage_path,
        rejection_reason: doc.rejection_reason,
        created_at: new Date(doc.created_at).toLocaleDateString()
      }));
      setDocuments(mappedDocs);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve driver profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleConfirmDelete = async () => {
    setDeleting(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      success('Driver Removed', `Successfully archived profile for ${driver.name}.`);
      setDeleteModalOpen(false);
      navigate('/dashboard/drivers');
    } catch (e) {
      error('Delete Error', 'Failed to remove driver.');
    } finally {
      setDeleting(false);
    }
  };

  const handleAssignVehicle = async () => {
    if (!selectedVehicleId) return;
    setAssigning(true);
    try {
      await assignVehicle(driver.id, selectedVehicleId);
      const targetTruck = vehicles.find(v => v.id === Number(selectedVehicleId));
      setDriver(prev => ({
        ...prev,
        assignedTruck: targetTruck
      }));
      success('Vehicle Assigned', `Successfully assigned vehicle ${targetTruck.license_plate} to ${driver.name}.`);
      setAssignModalOpen(false);
    } catch (e) {
      error('Assignment Error', 'Failed to assign vehicle.');
    } finally {
      setAssigning(false);
    }
  };

  const handleVerifyDocument = async () => {
    if (verifyStatus === 'REJECTED' && !rejectionReason) {
      error('Rejection Reason Required', 'Please provide a reason for rejecting the document.');
      return;
    }
    try {
      await verifyDriverDocument(verifyingDoc.id, verifyStatus, rejectionReason);
      success('Verification Updated', `Document marked as ${verifyStatus.toLowerCase()}.`);
      setVerifyingDoc(null);
      setRejectionReason('');
      loadData(); // reload to get new driver status and updated doc
    } catch (e) {
      error('Verification Error', 'Failed to update document status.');
    }
  };

  const handleApproveDriver = async () => {
    setApproving(true);
    try {
      await approveDriver(driver.id, 'APPROVED');
      success('Driver Approved', `${driver.name} has been approved and activated.`);
      await loadData();
    } catch (e) {
      error('Approval Error', e.message || 'Failed to approve driver.');
    } finally {
      setApproving(false);
    }
  };

  const handleRejectDriver = async () => {
    if (!driverRejectionReason) {
      error('Rejection Reason Required', 'Please provide a reason for rejecting the driver.');
      return;
    }
    setApproving(true);
    try {
      await approveDriver(driver.id, 'REJECTED', driverRejectionReason);
      success('Driver Rejected', `${driver.name} has been rejected.`);
      setRejectModalOpen(false);
      setDriverRejectionReason('');
      await loadData();
    } catch (e) {
      error('Rejection Error', e.message || 'Failed to reject driver.');
    } finally {
      setApproving(false);
    }
  };

  // Check if all required documents are present and approved
  const requiredCategories = ['license_front', 'license_back', 'aadhaar_front', 'aadhaar_back', 'selfie'];
  const allDocsApproved = requiredCategories.every(cat => {
    const doc = documents.find(d => d.category === cat);
    return doc && doc.status === 'approved';
  });
  const hasRejectedDocs = documents.some(d => d.status === 'rejected');
  const hasMissingDocs = requiredCategories.some(cat => !documents.find(d => d.category === cat));

  const canApproveDriver =
    driver?.verification_status === 'PENDING_APPROVAL' &&
    allDocsApproved &&
    !hasRejectedDocs &&
    !hasMissingDocs;

  const getRiskVariant = (score) => {
    if (score > 60) return 'danger';
    if (score > 30) return 'warning';
    return 'success';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  if (err || !driver) {
    return (
      <ErrorState
        title="Driver Profile Not Found"
        message={err?.message || 'The requested driver profile could not be loaded.'}
        onRetry={loadData}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigate('/dashboard/drivers')}
          />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-content">{driver.name}</h1>
              <Badge variant={driver.status === 'ACTIVE' ? 'success' : 'neutral'} dot>
                {driver.status === 'ACTIVE' ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <p className="text-sm text-content-secondary mt-0.5 flex items-center gap-1">
              <Phone className="h-3.5 w-3.5 text-content-muted" />
              {driver.phone_number}
              {driver.age && <span className="ml-2 text-content-muted">• Age: {driver.age}</span>}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            icon={<Edit2 className="h-4 w-4" />}
            onClick={() => navigate(`/dashboard/drivers/${driver.id}/edit`)}
          >
            Edit Profile
          </Button>
          <Button
            variant="danger"
            icon={<Trash2 className="h-4 w-4" />}
            onClick={() => setDeleteModalOpen(true)}
          >
            Delete
          </Button>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-muted tracking-wider uppercase">Safety Score</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-extrabold text-content">{driver.risk_score != null ? `${driver.risk_score} / 100` : 'N/A'}</span>
            <Badge variant={getRiskVariant(driver.risk_score)}>
              {driver.risk_score > 60 ? 'High Risk' : driver.risk_score > 30 ? 'Medium' : driver.risk_score != null ? 'Excellent' : 'Unrated'}
            </Badge>
          </div>
        </Card>

        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-muted tracking-wider uppercase">Rating</span>
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-1">
              <Star className="h-5 w-5 fill-amber-400 text-amber-400" />
              <span className="text-2xl font-extrabold text-content">{driver.rating != null ? Number(driver.rating).toFixed(1) : 'N/A'}</span>
            </div>
            <span className="text-xs text-content-secondary">Based on safety telemetry</span>
          </div>
        </Card>

        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-muted tracking-wider uppercase">Total Trips</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-extrabold text-content">{driver.total_trips ?? 0}</span>
            <span className="text-xs text-content-secondary">All-time dispatches</span>
          </div>
        </Card>

        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-muted tracking-wider uppercase">Onboarding Status</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-lg font-extrabold text-content">
              {driver.verification_status === 'APPROVED' ? 'Approved' : 
               driver.verification_status === 'PENDING_APPROVAL' ? 'Pending Approval' :
               driver.verification_status === 'PENDING_DOCUMENTS' ? 'Pending Docs' :
               driver.verification_status === 'REJECTED' ? 'Rejected' : 'Not Started'}
            </span>
            <Badge variant={
              driver.verification_status === 'APPROVED' ? 'success' :
              driver.verification_status === 'PENDING_APPROVAL' ? 'warning' :
              driver.verification_status === 'REJECTED' ? 'danger' : 'neutral'
            }>
              {driver.verification_status === 'APPROVED' ? <CheckCircle className="h-3.5 w-3.5" /> : 
               driver.verification_status === 'PENDING_APPROVAL' ? <Clock className="h-3.5 w-3.5" /> :
               <AlertTriangle className="h-3.5 w-3.5" />}
            </Badge>
          </div>
        </Card>

        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-muted tracking-wider uppercase">Total Expenses Logging</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-extrabold text-content">₹{(driver.total_expenses ?? 0).toLocaleString()}</span>
            <span className="text-xs text-content-secondary">WhatsApp verified</span>
          </div>
        </Card>
      </div>

      {/* Driver Approval Banner */}
      {canApproveDriver && (
        <Card className="p-4 border-2 border-green-200 bg-green-50/50">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-100">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-green-900">Ready for Final Approval</h3>
                <p className="text-xs text-green-700">All 5 required documents have been verified and approved.</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="border-red-200 text-red-700 hover:bg-red-50"
                icon={<XCircle className="h-4 w-4" />}
                onClick={() => setRejectModalOpen(true)}
              >
                Reject Driver
              </Button>
              <Button
                variant="primary"
                size="sm"
                icon={<CheckCircle className="h-4 w-4" />}
                onClick={handleApproveDriver}
                loading={approving}
              >
                Approve Driver
              </Button>
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Allocated Vehicle Card */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Truck className="h-4 w-4 text-brand-600" />
              Allocated Truck
            </CardTitle>
          </CardHeader>
          {driver.assignedTruck ? (
            <div className="space-y-4">
              <div className="p-4 bg-surface-secondary border border-border rounded-xl">
                <span className="text-[10px] font-bold text-content-secondary block uppercase">License Plate</span>
                <span className="text-lg font-bold font-mono text-content mt-1 block">
                  {driver.assignedTruck.license_plate}
                </span>
                <p className="text-xs text-content-secondary mt-1">
                  {driver.assignedTruck.make} {driver.assignedTruck.model} ({driver.assignedTruck.year})
                </p>
              </div>

              <div className="flex justify-between items-center text-sm py-1 border-b border-border">
                <span className="text-content-secondary">Tank Capacity</span>
                <span className="font-semibold text-content">{driver.assignedTruck.tank_capacity} Liters</span>
              </div>

              <Button
                variant="outline"
                className="w-full mt-2"
                onClick={() => {
                  setSelectedVehicleId(String(driver.assignedTruck.id));
                  setAssignModalOpen(true);
                }}
              >
                Change Assignment
              </Button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 border border-dashed border-border rounded-xl text-center space-y-3">
              <Truck className="h-8 w-8 text-content-muted" />
              <div>
                <p className="text-sm font-semibold text-content">No Assigned Truck</p>
                <p className="text-xs text-content-secondary mt-0.5 max-w-xs">
                  This operator is not currently linked to any fleet truck.
                </p>
              </div>
              <Button variant="primary" size="sm" onClick={() => setAssignModalOpen(true)}>
                Allocate Vehicle
              </Button>
            </div>
          )}
        </Card>

        {/* Driver Credentials Documents Card */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4 text-brand-600" />
              Credentials Documents Verification
            </CardTitle>
          </CardHeader>
          <div className="space-y-4">
            {/* System-level documents */}
            {documents.length === 0 ? (
              <div className="text-sm text-content-secondary py-4">No documents uploaded.</div>
            ) : documents.map((doc) => (
              <div
                key={doc.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 bg-surface border border-border rounded-xl hover:border-brand-300 transition-colors gap-3"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-surface-secondary text-content-secondary mt-0.5">
                    {doc.url ? (
                      <img src={doc.url} alt={doc.name} className="h-10 w-10 object-cover rounded" onError={(e) => { e.target.style.display = 'none'; }} />
                    ) : (
                      <FileText className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-content">{doc.name}</h4>
                    <span className="text-xs text-content-secondary mt-0.5 block flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-content-muted" />
                      Uploaded: {doc.created_at}
                    </span>
                    {doc.rejection_reason && (
                      <span className="text-xs text-red-600 mt-0.5 block">
                        Rejected: {doc.rejection_reason}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Badge variant={doc.status === 'approved' ? 'success' : doc.status === 'rejected' ? 'danger' : 'warning'}>
                    {doc.status.toUpperCase()}
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<CheckCircle className="h-3.5 w-3.5 text-brand-600" />}
                    onClick={() => {
                      setVerifyingDoc(doc);
                      setVerifyStatus('');
                      setRejectionReason('');
                    }}
                  >
                    Verify
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Verify Document Modal */}
      <Modal
        open={!!verifyingDoc}
        onClose={() => setVerifyingDoc(null)}
        title="Verify Document"
        description={`Review the document for ${verifyingDoc?.name}`}
        footer={
          <>
            <Button variant="outline" onClick={() => setVerifyingDoc(null)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleVerifyDocument} 
              disabled={!verifyStatus || (verifyStatus === 'REJECTED' && !rejectionReason)}
            >
              Confirm
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {verifyingDoc?.url && (
            <div className="flex justify-center bg-surface-secondary p-2 rounded-lg border border-border">
              <img src={verifyingDoc.url} alt="Document preview" className="max-h-64 object-contain rounded" />
            </div>
          )}
          
          <div className="space-y-2">
            <label className="block text-sm font-medium text-content-secondary">
              Verification Decision
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input 
                  type="radio" 
                  name="status" 
                  value="APPROVED" 
                  checked={verifyStatus === 'APPROVED'} 
                  onChange={(e) => setVerifyStatus(e.target.value)} 
                />
                <span className="text-sm font-medium text-green-700">Approve</span>
              </label>
              <label className="flex items-center gap-2">
                <input 
                  type="radio" 
                  name="status" 
                  value="REJECTED" 
                  checked={verifyStatus === 'REJECTED'} 
                  onChange={(e) => setVerifyStatus(e.target.value)} 
                />
                <span className="text-sm font-medium text-red-700">Reject</span>
              </label>
            </div>
          </div>

          {verifyStatus === 'REJECTED' && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-content-secondary">
                Rejection Reason (Required)
              </label>
              <input
                type="text"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="e.g. Image is blurry, name mismatch..."
                className="w-full h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
            </div>
          )}
        </div>
      </Modal>

      {/* Driver Rejection Modal */}
      <Modal
        open={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title="Reject Driver"
        description={`Reject the driver account for ${driver?.name}`}
        closable={!approving}
        footer={
          <>
            <Button variant="outline" onClick={() => setRejectModalOpen(false)} disabled={approving}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleRejectDriver} loading={approving} disabled={!driverRejectionReason}>
              Reject Driver
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 rounded-xl">
            <ShieldAlert className="h-5 w-5 text-red-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-red-950">
                This will reject the driver's account
              </p>
              <p className="text-xs text-red-700">
                The driver will remain inactive and will be notified of the rejection reason.
              </p>
            </div>
          </div>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-content-secondary">
              Rejection Reason (Required)
            </label>
            <input
              type="text"
              value={driverRejectionReason}
              onChange={(e) => setDriverRejectionReason(e.target.value)}
              placeholder="e.g. Documents do not match, identity verification failed..."
              className="w-full h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />
          </div>
        </div>
      </Modal>

      {/* Allocation Selection Modal */}
      <Modal
        open={assignModalOpen}
        onClose={() => setAssignModalOpen(false)}
        title="Allocate Fleet Truck"
        description={`Link a vehicle to ${driver.name} for upcoming operations.`}
        closable={!assigning}
        footer={
          <>
            <Button variant="outline" onClick={() => setAssignModalOpen(false)} disabled={assigning}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleAssignVehicle} loading={assigning} disabled={!selectedVehicleId}>
              Confirm Allocation
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <label className="block text-sm font-medium text-content-secondary">
            Select Active Vehicle
          </label>
          <select
            value={selectedVehicleId}
            onChange={(e) => setSelectedVehicleId(e.target.value)}
            className="w-full h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          >
            <option value="">-- Choose Truck --</option>
            {vehicles.map(v => (
              <option key={v.id} value={v.id}>
                {v.license_plate} - {v.make} {v.model}
              </option>
            ))}
          </select>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Driver Profile"
        description="Are you sure you want to remove this driver profile? This action will archive safety ratings."
        closable={!deleting}
        footer={
          <>
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleConfirmDelete} loading={deleting}>
              Delete
            </Button>
          </>
        }
      >
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 rounded-xl">
          <ShieldAlert className="h-5 w-5 text-red-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-950">
              Removing {driver.name}
            </p>
            <p className="text-xs text-red-700">
              This will permanently revoke dispatch allocations and archive security credentials.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
