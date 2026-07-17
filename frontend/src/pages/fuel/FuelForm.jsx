import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Fuel } from 'lucide-react';
import { createFuelEntry } from '@/api/fuelApi';
import { getVehicles } from '@/api/vehicleApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input, Select } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';

export default function FuelForm() {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  // Form states
  const [vehicleId, setVehicleId] = useState('');
  const [quantityLiters, setQuantityLiters] = useState('');
  const [pricePerLiter, setPricePerLiter] = useState('');
  const [odometer, setOdometer] = useState('');
  const [station, setStation] = useState('');
  const [uploadingReceipt, setUploadingReceipt] = useState(false);
  const [receiptUrl, setReceiptUrl] = useState('');

  const [errors, setErrors] = useState({});

  const loadVehicles = async () => {
    setFetching(true);
    setFetchError(null);
    try {
      const data = await getVehicles({ status: 'active' });
      setVehicles(data);
    } catch (e) {
      setFetchError(e);
      error('Load Error', 'Failed to retrieve active vehicles.');
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    loadVehicles();
  }, []);

  const totalCalculated = (Number(quantityLiters || 0) * Number(pricePerLiter || 0));

  const validate = () => {
    const errs = {};
    if (!vehicleId) errs.vehicleId = 'Vehicle choice is required';
    if (!station.trim()) errs.station = 'Gas station location is required';

    if (!quantityLiters) {
      errs.quantityLiters = 'Volume quantity is required';
    } else if (Number(quantityLiters) <= 0) {
      errs.quantityLiters = 'Volume must be greater than 0';
    }

    if (!pricePerLiter) {
      errs.pricePerLiter = 'Price rate per liter is required';
    } else if (Number(pricePerLiter) <= 0) {
      errs.pricePerLiter = 'Rate must be greater than 0';
    }

    if (!odometer) {
      errs.odometer = 'Odometer logging is required';
    } else if (Number(odometer) <= 0) {
      errs.odometer = 'Odometer must be positive';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSimulateUpload = async () => {
    setUploadingReceipt(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      setReceiptUrl('https://example.com/receipts/fuel_' + Math.floor(Math.random() * 1000) + '.jpg');
      success('Receipt Uploaded', 'Fuel slip attached successfully.');
    } catch (e) {
      error('Upload Failed', 'Failed to scan slip.');
    } finally {
      setUploadingReceipt(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);

    const selectedTruck = vehicles.find(v => v.id === Number(vehicleId));

    const payload = {
      truck_id: Number(vehicleId),
      truck_plate: selectedTruck?.license_plate || '',
      quantity_liters: Number(quantityLiters),
      price_per_liter: Number(pricePerLiter),
      total_amount: totalCalculated,
      odometer: Number(odometer),
      station: station.trim(),
      receipt_url: receiptUrl
    };

    try {
      await createFuelEntry(payload);
      success('Fuel Entry Saved', `Refueling logged for vehicle ${payload.truck_plate}.`);
      navigate('/dashboard/fuel');
    } catch (e) {
      error('Save Failed', e.message || 'Failed to submit fuel entry.');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  if (fetchError) {
    return (
      <ErrorState
        title="Resources Error"
        message="Could not load vehicle profiles to match refueling logs."
        onRetry={loadVehicles}
      />
    );
  }

  const vehicleOptions = vehicles.map(v => ({ value: v.id, label: `${v.license_plate} - ${v.make} ${v.model}` }));

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Title */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          icon={<ArrowLeft className="h-4 w-4" />}
          onClick={() => navigate('/dashboard/fuel')}
        />
        <div>
          <h1 className="text-2xl font-bold text-content">Add Refuel Entry</h1>
          <p className="text-sm text-content-secondary mt-0.5">Log fuel card transactions and match odometer specifications.</p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select
            label="Allocate Vehicle"
            placeholder="-- Select Truck --"
            options={vehicleOptions}
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
            error={errors.vehicleId}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Fuel Quantity (Liters)"
              type="number"
              min="1"
              placeholder="e.g. 150"
              value={quantityLiters}
              onChange={(e) => setQuantityLiters(e.target.value)}
              error={errors.quantityLiters}
              required
            />
            <Input
              label="Price Per Liter (INR)"
              type="number"
              min="1"
              step="0.01"
              placeholder="e.g. 94.50"
              value={pricePerLiter}
              onChange={(e) => setPricePerLiter(e.target.value)}
              error={errors.pricePerLiter}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Total Cost Amount (Auto-Calculated)"
              type="text"
              value={totalCalculated > 0 ? `₹ ${totalCalculated.toLocaleString()}` : ''}
              disabled
              className="bg-surface-secondary cursor-not-allowed font-semibold text-content"
            />
            <Input
              label="Odometer Log Value (km)"
              type="number"
              placeholder="e.g. 124500"
              value={odometer}
              onChange={(e) => setOdometer(e.target.value)}
              error={errors.odometer}
              required
            />
          </div>

          <Input
            label="Fuel Station & Location"
            placeholder="e.g. Jio-bp Udaipur, NH-48"
            value={station}
            onChange={(e) => setStation(e.target.value)}
            error={errors.station}
            required
          />

          {/* Receipt attachment */}
          <div className="space-y-1.5">
            <span className="block text-sm font-medium text-content-secondary">Refuel Slip receipt</span>
            <div className="flex items-center gap-3">
              <Button
                type="button"
                variant="outline"
                loading={uploadingReceipt}
                icon={<Fuel className="h-4 w-4 text-brand-600" />}
                onClick={handleSimulateUpload}
              >
                Scan Receipt Slip
              </Button>
              {receiptUrl ? (
                <span className="text-xs text-green-600 font-semibold">✓ Receipt attached successfully</span>
              ) : (
                <span className="text-xs text-content-secondary">No receipt attached</span>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/dashboard/fuel')}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              icon={<Save className="h-4 w-4" />}
              loading={loading}
            >
              Log Transaction
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
