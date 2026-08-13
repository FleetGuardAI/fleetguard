import React, { useState, useEffect, lazy, Suspense } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, Edit3, MapPin, Calendar, Clock, Route, CheckCircle, Navigation, Info, Brain } from 'lucide-react';
import { getTripById, updateTripStatus } from '@/api/tripApi';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';
import { Input, Select } from '@/components/ui/Input';
import './TripIntelligence.css';

const TripIntelligence = lazy(() => import('./TripIntelligence'));

export default function TripDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [trip, setTrip] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [activeTab, setActiveTab] = useState('details');

  // Status Modal states
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [statusDesc, setStatusDesc] = useState('');
  const [updating, setUpdating] = useState(false);

  const loadTrip = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getTripById(id);
      setTrip(data);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve trip details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTrip();
  }, [id]);

  const handleUpdateStatus = async () => {
    if (!newStatus) return;
    setUpdating(true);
    try {
      const updatedTrip = await updateTripStatus(trip.id, newStatus, statusDesc);
      setTrip(updatedTrip);
      success('Status Updated', `Successfully transition trip to status: ${newStatus.toUpperCase()}`);
      setStatusModalOpen(false);
      setNewStatus('');
      setStatusDesc('');
    } catch (e) {
      error('Update Error', 'Failed to update trip status.');
    } finally {
      setUpdating(false);
    }
  };

  const getStatusVariant = (status) => {
    if (status === 'on-trip') return 'brand';
    if (status === 'completed') return 'success';
    if (status === 'scheduled') return 'warning';
    return 'neutral';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  if (err || !trip) {
    return (
      <ErrorState
        title="Trip Not Found"
        message={err?.message || 'The requested trip record could not be loaded.'}
        onRetry={loadTrip}
      />
    );
  }

  const statusOptions = [
    { value: 'on-trip', label: 'On Trip / Active' },
    { value: 'completed', label: 'Completed' },
    { value: 'scheduled', label: 'Scheduled' }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            icon={<ArrowLeft className="h-4 w-4" />}
            onClick={() => navigate('/dashboard/trips')}
          />
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-content">{trip.route_name}</h1>
              <Badge variant={getStatusVariant(trip.status)}>
                {trip.status.toUpperCase()}
              </Badge>
            </div>
            <p className="text-xs text-content-secondary mt-1">
              Vehicle: <Link to={`/dashboard/vehicles/${trip.truck_id}`} className="font-mono underline text-brand-600 hover:text-brand-700">{trip.truck_plate}</Link> • Driver: {trip.driver_name}
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          icon={<Edit3 className="h-4 w-4" />}
          onClick={() => setStatusModalOpen(true)}
        >
          Update Status
        </Button>
      </div>

      {/* ══════ Tab Navigation ══════ */}
      <div className="ti-tab-nav">
        <button
          className={`ti-tab-btn ${activeTab === 'details' ? 'active' : ''}`}
          onClick={() => setActiveTab('details')}
        >
          Trip Details
        </button>
        <button
          className={`ti-tab-btn ${activeTab === 'intelligence' ? 'active' : ''}`}
          onClick={() => setActiveTab('intelligence')}
        >
          <span className="flex items-center gap-1.5">
            <Brain className="h-3.5 w-3.5" />
            Trip Intelligence
          </span>
        </button>
      </div>

      {/* ══════ Tab Content ══════ */}
      {activeTab === 'details' ? (
        <>
          {/* Stats Cards Grid — existing content preserved exactly */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="space-y-4 lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Info className="h-4 w-4 text-brand-600" />
                  Trip Manifest Specs
                </CardTitle>
              </CardHeader>
              <div className="space-y-3.5 text-sm">
                <div className="flex justify-between items-center py-1 border-b border-border">
                  <span className="text-content-secondary">Origin</span>
                  <span className="font-medium text-content">{trip.start_point}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-border">
                  <span className="text-content-secondary">Destination</span>
                  <span className="font-medium text-content">{trip.end_point}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-border">
                  <span className="text-content-secondary">Total Route Distance</span>
                  <span className="font-semibold text-content">{trip.distance_km} km</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-border">
                  <span className="text-content-secondary">Dispatch Timestamp</span>
                  <span className="font-medium text-content">{new Date(trip.start_date).toLocaleDateString()}</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-content-secondary">Delivery Date</span>
                  <span className="font-medium text-content">
                    {trip.end_date ? new Date(trip.end_date).toLocaleDateString() : `${new Date(trip.expected_delivery).toLocaleDateString()} (Est.)`}
                  </span>
                </div>
              </div>
            </Card>

            {/* Timeline Log Card */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Navigation className="h-4 w-4 text-brand-600 animate-pulse" />
                  Trip Timeline Track
                </CardTitle>
              </CardHeader>
              
              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
                {trip.timeline.map((item, idx) => {
                  const isLast = idx === trip.timeline.length - 1;
                  return (
                    <div key={idx} className="relative">
                      <div className={`absolute -left-6 top-1.5 w-3.5 h-3.5 rounded-full border-2 border-white dark:border-slate-800 shadow-sm ${isLast ? 'bg-brand-600 scale-110' : 'bg-content-muted'}`} />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-semibold ${isLast ? 'text-brand-600' : 'text-content'}`}>
                            {item.status}
                          </span>
                          <span className="text-[10px] text-content-secondary">
                            {new Date(item.time).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-xs text-content-secondary mt-1">{item.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          </div>

          {/* Telemetry coordinate map placeholder */}
          <Card className="flex flex-col items-center justify-center py-16 text-center border border-dashed">
            <Route className="h-10 w-10 text-content-muted mb-3 animate-pulse" />
            <h4 className="text-sm font-semibold text-content">GPS Telemetry Coordinates</h4>
            <p className="text-xs text-content-secondary mt-1 max-w-sm">
              Active coordinate location match: Lat {trip.current_lat || '22.572'}, Lng {trip.current_lng || '72.977'}.
            </p>
          </Card>
        </>
      ) : (
        /* ══════ Trip Intelligence Tab ══════ */
        <Suspense fallback={
          <div className="flex items-center justify-center py-24">
            <Loader size="lg" />
          </div>
        }>
          <TripIntelligence tripId={trip.id} trip={trip} />
        </Suspense>
      )}

      {/* Update Status Modal — always available regardless of tab */}
      <Modal
        open={statusModalOpen}
        onClose={() => setStatusModalOpen(false)}
        title="Update Trip Status"
        description="Select next state checkpoint and add update notes."
        closable={!updating}
        footer={
          <>
            <Button variant="outline" onClick={() => setStatusModalOpen(false)} disabled={updating}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleUpdateStatus} loading={updating} disabled={!newStatus}>
              Submit Update
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); handleUpdateStatus(); }}>
          <Select
            label="Target Status"
            placeholder="-- Choose Status --"
            options={statusOptions}
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value)}
            required
          />

          <Input
            label="Timeline Description Notes"
            placeholder="e.g. Checked in at Udaipur weighbridge; cargo status OK."
            value={statusDesc}
            onChange={(e) => setStatusDesc(e.target.value)}
          />
        </form>
      </Modal>
    </div>
  );
}
