import React, { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/Toast';
import { updateHardwareDevice } from '@/api/assetApi';

export default function EditDeviceModal({ open, onClose, device, onSuccess }) {
  const { success, error: toastError } = useToast();

  const [deviceName, setDeviceName] = useState('');
  const [manufacturer, setManufacturer] = useState('');
  const [model, setModel] = useState('');
  const [protocol, setProtocol] = useState('');
  const [gpsProvider, setGpsProvider] = useState('');
  const [offlineThreshold, setOfflineThreshold] = useState(15);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (device) {
      setDeviceName(device.device_name || '');
      setManufacturer(device.manufacturer || '');
      setModel(device.model || '');
      setProtocol(device.protocol || '');
      setGpsProvider(device.gps_provider || '');
      setOfflineThreshold(device.offline_threshold_minutes || 15);
    }
  }, [device]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!device) return;
    setSubmitting(true);
    try {
      await updateHardwareDevice(device.id, {
        device_name: deviceName.trim(),
        manufacturer: manufacturer.trim() || undefined,
        model: model.trim() || undefined,
        protocol: protocol || undefined,
        gps_provider: gpsProvider.trim() || undefined,
        offline_threshold_minutes: parseInt(offlineThreshold, 10) || 15,
      });
      success('Device Updated', `Settings for "${deviceName}" have been saved.`);
      onSuccess?.();
      onClose();
    } catch (err) {
      console.error(err);
      toastError('Update Failed', err.message || 'Unable to update device parameters.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="md"
      title={`Edit Device: ${device?.device_name || ''}`}
      description={`IMEI: ${device?.imei || ''}`}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-content mb-1">Device Label / Name</label>
          <input
            type="text"
            required
            value={deviceName}
            onChange={(e) => setDeviceName(e.target.value)}
            className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-content mb-1">Manufacturer</label>
            <input
              type="text"
              value={manufacturer}
              onChange={(e) => setManufacturer(e.target.value)}
              className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-content mb-1">Model</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-content mb-1">Protocol Identifier</label>
            <input
              type="text"
              value={protocol}
              onChange={(e) => setProtocol(e.target.value)}
              className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm font-mono text-xs"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-content mb-1">GPS Provider</label>
            <input
              type="text"
              value={gpsProvider}
              onChange={(e) => setGpsProvider(e.target.value)}
              className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-content mb-1">
            Offline Threshold (Minutes)
          </label>
          <input
            type="number"
            min={1}
            max={1440}
            value={offlineThreshold}
            onChange={(e) => setOfflineThreshold(e.target.value)}
            className="w-full h-10 px-3 border border-border rounded-lg bg-surface text-content text-sm"
          />
          <p className="text-[11px] text-content-muted mt-1">
            Duration of silence before device is marked as "Disconnected".
          </p>
        </div>

        <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
          <Button variant="ghost" type="button" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={submitting}
            icon={submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          >
            {submitting ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
