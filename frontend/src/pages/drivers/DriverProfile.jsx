import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Edit2, Trash2, Phone, Star, ShieldAlert, Truck, FileText, Upload, Calendar, RefreshCw } from 'lucide-react';
import { getDriverById, assignVehicle } from '@/api/driverApi';
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

  // Mock doc list
  const [documents, setDocuments] = useState([
    { id: 1, name: 'Commercial Driving License', status: 'verified', expiry: '2028-11-20' },
    { id: 2, name: 'Medical Fitness Certificate', status: 'warning', expiry: '2026-08-15' },
    { id: 3, name: 'Aadhaar Card Copy', status: 'verified', expiry: 'N/A' }
  ]);
  const [uploadingDoc, setUploadingDoc] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setErr(null);
    try {
      const d = await getDriverById(id);
      setDriver(d);
      const v = await getVehicles();
      setVehicles(v);
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

  const handleUploadDocument = async (docName) => {
    setUploadingDoc(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setDocuments(prev => prev.map(doc => 
        doc.name === docName 
          ? { ...doc, status: 'verified', expiry: '2029-01-01' } 
          : doc
      ));
      success('Upload Successful', `Renewed ${docName} successfully.`);
    } catch (e) {
      error('Upload Failed', 'Failed to submit document.');
    } finally {
      setUploadingDoc(false);
    }
  };

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
              <Badge variant={driver.is_active ? 'success' : 'neutral'} dot>
                {driver.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <p className="text-sm text-content-secondary mt-0.5 flex items-center gap-1">
              <Phone className="h-3.5 w-3.5 text-content-muted" />
              {driver.phone_number}
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
            <span className="text-2xl font-extrabold text-content">{driver.risk_score} / 100</span>
            <Badge variant={getRiskVariant(driver.risk_score)}>
              {driver.risk_score > 60 ? 'High Risk' : driver.risk_score > 30 ? 'Medium' : 'Excellent'}
            </Badge>
          </div>
        </Card>

        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-muted tracking-wider uppercase">Rating</span>
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-1">
              <Star className="h-5 w-5 fill-amber-400 text-amber-400" />
              <span className="text-2xl font-extrabold text-content">{driver.rating.toFixed(1)}</span>
            </div>
            <span className="text-xs text-content-secondary">Based on safety telemetry</span>
          </div>
        </Card>

        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-muted tracking-wider uppercase">Total Trips</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-extrabold text-content">{driver.total_trips ?? 148}</span>
            <span className="text-xs text-content-secondary">All-time dispatches</span>
          </div>
        </Card>

        <Card className="flex flex-col justify-between p-4">
          <span className="text-[10px] font-bold text-content-muted tracking-wider uppercase">Total Expenses Logging</span>
          <div className="flex items-baseline justify-between mt-2">
            <span className="text-2xl font-extrabold text-content">₹{(driver.total_expenses ?? 125600).toLocaleString()}</span>
            <span className="text-xs text-content-secondary">WhatsApp verified</span>
          </div>
        </Card>
      </div>

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
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 bg-surface border border-border rounded-xl hover:border-brand-300 transition-colors gap-3"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-surface-secondary text-content-secondary mt-0.5">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-content">{doc.name}</h4>
                    <span className="text-xs text-content-secondary mt-0.5 block flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-content-muted" />
                      Expiry: {doc.expiry}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Badge variant={doc.status === 'verified' ? 'success' : 'warning'}>
                    {doc.status.toUpperCase()}
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    loading={uploadingDoc}
                    icon={<Upload className="h-3.5 w-3.5 text-brand-600" />}
                    onClick={() => handleUploadDocument(doc.name)}
                  >
                    Upload Renew
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

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
        <div className="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30 rounded-xl">
          <ShieldAlert className="h-5 w-5 text-red-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-950 dark:text-red-400">
              Removing {driver.name}
            </p>
            <p className="text-xs text-red-700 dark:text-red-300">
              This will permanently revoke dispatch allocations and archive security credentials.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
