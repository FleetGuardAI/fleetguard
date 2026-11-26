import React, { useState, useMemo } from 'react';
import { Truck, Check, AlertTriangle, Cpu, RefreshCw } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/components/ui/Toast';
import { reassignDeviceVehicle, disconnectHardwareDevice } from '@/api/assetApi';

export default function ReassignVehicleModal({ open, onClose, device, vehicles = [], onSuccess }) {
  const { success, error: toastError } = useToast();

  const [mode, setMode] = useState('REASSIGN'); // 'REASSIGN' | 'STORAGE'
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const [force, setForce] = useState(false);
  const [search, setSearch] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const filteredVehicles = useMemo(() => {
    if (!search.trim()) return vehicles;
    const q = search.toLowerCase();
    return vehicles.filter(v =>
      (v.registration_number || v.license_plate || '').toLowerCase().includes(q) ||
      (v.make || '').toLowerCase().includes(q) ||
      (v.model || '').toLowerCase().includes(q)
    );
  }, [vehicles, search]);

  const selectedVehicle = useMemo(() => {
    return vehicles.find(v => v.id === selectedVehicleId);
  }, [vehicles, selectedVehicleId]);

  const hasConflict = useMemo(() => {
    if (!selectedVehicle) return false;
    // Check if vehicle has an active device that is not the current device
    return (
      (selectedVehicle.has_active_gps || selectedVehicle.current_device_id) &&
      selectedVehicle.current_device_id !== device?.id
    );
  }, [selectedVehicle, device]);

  const handleSubmit = async () => {
    if (!device) return;
    setSubmitting(true);
    try {
      if (mode === 'STORAGE') {
        await disconnectHardwareDevice(device.id);
        success('Device Disconnected', `Device "${device.device_name}" unassigned and moved to storage.`);
      } else {
        if (!selectedVehicleId) {
          toastError('Selection Required', 'Please select a vehicle to assign this device to.');
          setSubmitting(false);
          return;
        }
        await reassignDeviceVehicle(device.id, {
          vehicle_id: selectedVehicleId,
          force: force,
        });
        success('Vehicle Reassigned', `Device "${device.device_name}" assigned to ${selectedVehicle?.registration_number}.`);
      }
      onSuccess?.();
      onClose();
    } catch (err) {
      console.error(err);
      toastError('Reassignment Failed', err.message || 'Unable to update vehicle assignment.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="md"
      title={`Reassign Hardware Device: ${device?.device_name || ''}`}
      description={`Currently assigned to: ${device?.vehicle_registration || 'Unassigned (Storage)'}`}
    >
      <div className="space-y-4">
        {/* Toggle Mode */}
        <div className="grid grid-cols-2 gap-3">
          <div
            onClick={() => setMode('REASSIGN')}
            className={`p-3 rounded-xl border-2 cursor-pointer flex items-center gap-2.5 transition-colors ${
              mode === 'REASSIGN' ? 'border-brand-500 bg-brand-50/30' : 'border-border bg-surface'
            }`}
          >
            <Truck className="w-4 h-4 text-brand-600" />
            <div>
              <p className="text-xs font-semibold text-content">Mount to Vehicle</p>
              <p className="text-[10px] text-content-muted">Assign to active fleet truck</p>
            </div>
          </div>

          <div
            onClick={() => {
              setMode('STORAGE');
              setSelectedVehicleId(null);
            }}
            className={`p-3 rounded-xl border-2 cursor-pointer flex items-center gap-2.5 transition-colors ${
              mode === 'STORAGE' ? 'border-brand-500 bg-brand-50/30' : 'border-border bg-surface'
            }`}
          >
            <Cpu className="w-4 h-4 text-content-secondary" />
            <div>
              <p className="text-xs font-semibold text-content">Unassign to Storage</p>
              <p className="text-[10px] text-content-muted">Move device to inventory</p>
            </div>
          </div>
        </div>

        {mode === 'REASSIGN' && (
          <div className="space-y-3">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter vehicle registration number..."
              className="w-full h-9 px-3 border border-border rounded-lg bg-surface text-content text-xs"
            />

            <div className="max-h-52 overflow-y-auto border border-border rounded-xl divide-y divide-border bg-surface">
              {filteredVehicles.length === 0 ? (
                <div className="p-3 text-center text-xs text-content-muted">No vehicles available.</div>
              ) : (
                filteredVehicles.map(v => {
                  const isSelected = selectedVehicleId === v.id;
                  const isCurrent = v.id === device?.current_vehicle_id;
                  return (
                    <div
                      key={v.id}
                      onClick={() => setSelectedVehicleId(v.id)}
                      className={`p-2.5 flex items-center justify-between cursor-pointer transition-colors ${
                        isSelected ? 'bg-brand-50' : 'hover:bg-surface-secondary'
                      }`}
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-content">
                            {v.registration_number || v.license_plate}
                          </span>
                          {isCurrent && <Badge variant="neutral" size="sm">Current</Badge>}
                          {v.has_active_gps && !isCurrent && (
                            <Badge variant="warning" size="sm">Has GPS</Badge>
                          )}
                        </div>
                        <span className="text-[11px] text-content-muted">
                          {[v.make, v.model].filter(Boolean).join(' ') || 'Standard Truck'}
                        </span>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-brand-600" />}
                    </div>
                  );
                })
              )}
            </div>

            {hasConflict && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl space-y-2">
                <div className="flex items-start gap-2 text-xs text-amber-800">
                  <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    Vehicle <strong>{selectedVehicle?.registration_number}</strong> already has an active GPS tracker.
                  </div>
                </div>
                <label className="flex items-center gap-2 text-xs text-amber-900 cursor-pointer pl-6">
                  <input
                    type="checkbox"
                    checked={force}
                    onChange={(e) => setForce(e.target.checked)}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span>Force swap: automatically unassign existing tracker to storage</span>
                </label>
              </div>
            )}
          </div>
        )}

        {mode === 'STORAGE' && (
          <div className="p-4 bg-surface-secondary rounded-xl border border-border text-xs text-content-secondary space-y-1">
            <p className="font-semibold text-content">Non-Destructive Storage Operation</p>
            <p>
              Moving this device to storage will unassign it from vehicle{' '}
              <strong>{device?.vehicle_registration || 'current truck'}</strong>. All historical GPS telemetry records,
              trips, and odometer logs remain intact in the database.
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
          <Button variant="ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={submitting || (mode === 'REASSIGN' && !selectedVehicleId) || (mode === 'REASSIGN' && hasConflict && !force)}
            icon={submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
          >
            {submitting ? 'Updating...' : mode === 'STORAGE' ? 'Move to Storage' : 'Confirm Assignment'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
