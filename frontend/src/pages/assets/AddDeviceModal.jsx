import React, { useState, useEffect, useRef } from 'react';
import { Eye, EyeOff, Check, AlertCircle } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { createHardwareAsset } from '@/api/assetApi';
import { useToast } from '@/components/ui/Toast';

export default function AddDeviceModal({ open, onClose, onSuccess, vehicles = [] }) {
  const { success, error } = useToast();

  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  
  const [deviceName, setDeviceName] = useState('');

  // Vehicle Autocomplete state
  const [vehicleSearch, setVehicleSearch] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const wrapperRef = useRef(null);

  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState('');

  // Reset state on open
  useEffect(() => {
    if (open) {
      setApiKey('');
      setShowApiKey(false);
      setDeviceName('');
      setVehicleSearch('');
      setSelectedVehicle(null);
      setShowSuggestions(false);
      setSubmitError('');
      setLoading(false);
    }
  }, [open]);

  // Click outside to close suggestions
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleVehicleSelect = (v) => {
    setSelectedVehicle(v);
    setVehicleSearch(v.registration_number || v.license_plate || `Vehicle ${v.id}`);
    setShowSuggestions(false);
  };

  const filteredVehicles = React.useMemo(() => {
    if (!vehicleSearch.trim()) return [];
    const q = vehicleSearch.toLowerCase().trim();
    return vehicles.filter(v => {
      const plate = (v.registration_number || v.license_plate || '').toLowerCase();
      return plate.includes(q);
    });
  }, [vehicleSearch, vehicles]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError('');

    const key = apiKey.trim();
    const name = deviceName.trim();

    if (!key) {
      setSubmitError('API Key is required.');
      return;
    }
    if (!selectedVehicle) {
      setSubmitError('Please select a valid vehicle from the suggestions.');
      return;
    }
    if (!name) {
      setSubmitError('Device Name is required.');
      return;
    }

    setLoading(true);
    try {
      await createHardwareAsset({
        api_key: key,
        vehicle_id: selectedVehicle.id,
        device_name: name
      });
      success('Device added successfully', `Hardware asset "${name}" has been registered.`);
      onSuccess();
    } catch (err) {
      console.error(err);
      if (err.message?.includes('duplicate') || err.message?.includes('already connected')) {
        setSubmitError('This device is already connected to a vehicle.');
      } else {
        setSubmitError(err.message || 'An error occurred while creating the device.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={loading ? undefined : onClose}
      title="Add Device"
      description="Connect a new hardware/telematics device to your fleet."
      closable={!loading}
      maxWidth="sm"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {submitError && (
          <div className="p-3 rounded-lg bg-danger-50 border border-danger-200 flex gap-2 items-start text-danger-700 text-sm">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{submitError}</span>
          </div>
        )}

        {/* API KEY FIELD */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-content">
            API Key <span className="text-danger">*</span>
          </label>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter device API key"
              className="w-full h-10 px-3 pr-10 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              required
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-content-secondary hover:text-content"
              tabIndex={-1}
            >
              {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-xs text-content-muted mt-1">
            Your API key is stored securely and used only to connect this device.
          </p>
        </div>

        {/* VEHICLE AUTOCOMPLETE */}
        <div className="space-y-1" ref={wrapperRef}>
          <label className="block text-sm font-medium text-content">
            Vehicle Number <span className="text-danger">*</span>
          </label>
          <div className="relative">
            <input
              type="text"
              value={vehicleSearch}
              onChange={(e) => {
                setVehicleSearch(e.target.value);
                setSelectedVehicle(null); // Clear selection if typing manually
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              placeholder="Search vehicle (e.g. RJ19UF1234)"
              className="w-full h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
              required
            />
            
            {showSuggestions && vehicleSearch.trim().length > 0 && (
              <div className="absolute z-50 w-full mt-1 bg-surface border border-border rounded-lg shadow-lg overflow-hidden max-h-48 overflow-y-auto">
                {filteredVehicles.length > 0 ? (
                  <ul className="py-1">
                    {filteredVehicles.map(v => {
                      const plate = v.registration_number || v.license_plate || `ID: ${v.id}`;
                      const isSelected = selectedVehicle?.id === v.id;
                      return (
                        <li
                          key={v.id}
                          className={`px-3 py-2 text-sm cursor-pointer hover:bg-surface-secondary transition-colors ${isSelected ? 'bg-primary/5 text-primary' : 'text-content'}`}
                          onClick={() => handleVehicleSelect(v)}
                        >
                          <div className="flex justify-between items-center">
                            <span className="font-medium font-mono">{plate}</span>
                            {isSelected && <Check className="w-4 h-4" />}
                          </div>
                          <div className="text-xs text-content-muted mt-0.5">
                            {[v.make, v.model].filter(Boolean).join(' ')} · {v.status || 'Active'}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <div className="p-3 text-sm text-content-muted text-center italic">
                    No matching vehicles found
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* DEVICE NAME FIELD */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-content">
            Device Name <span className="text-danger">*</span>
          </label>
          <input
            type="text"
            value={deviceName}
            onChange={(e) => setDeviceName(e.target.value)}
            placeholder="Enter device name (e.g. Tata GPS Unit)"
            maxLength={100}
            className="w-full h-10 px-3 border border-border bg-surface text-content text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            required
          />
        </div>

        {/* ACTIONS */}
        <div className="pt-4 flex justify-end gap-3 border-t border-border mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={loading}
          >
            Add Device
          </Button>
        </div>
      </form>
    </Modal>
  );
}
