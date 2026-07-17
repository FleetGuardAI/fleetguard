import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { getVehicleById, createVehicle, updateVehicle } from '@/api/vehicleApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';

export default function VehicleForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { success, error } = useToast();

  const isEdit = Boolean(id);

  const [licensePlate, setLicensePlate] = useState('');
  const [make, setMake] = useState('');
  const [model, setModel] = useState('');
  const [year, setYear] = useState(new Date().getFullYear());
  const [tankCapacity, setTankCapacity] = useState('');

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);
  const [fetchError, setFetchError] = useState(null);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (isEdit) {
      const fetchVehicle = async () => {
        setFetching(true);
        setFetchError(null);
        try {
          const v = await getVehicleById(id);
          setLicensePlate(v.license_plate);
          setMake(v.make);
          setModel(v.model);
          setYear(v.year);
          setTankCapacity(v.tank_capacity);
        } catch (e) {
          setFetchError(e);
          error('Load Failed', 'Could not retrieve vehicle details.');
        } finally {
          setFetching(false);
        }
      };
      fetchVehicle();
    }
  }, [id, isEdit]);

  const validate = () => {
    const errs = {};
    if (!licensePlate.trim()) {
      errs.licensePlate = 'License plate is required';
    } else if (!/^[A-Z]{2}[0-9]{2}[A-Z\s]{0,3}[0-9]{4}$/i.test(licensePlate.trim())) {
      errs.licensePlate = 'Invalid format. Example: RJ14 XX 1234';
    }

    if (!make.trim()) errs.make = 'Manufacturer / Make is required';
    if (!model.trim()) errs.model = 'Model is required';

    const currentYear = new Date().getFullYear();
    if (!year) {
      errs.year = 'Year of manufacture is required';
    } else if (year < 2000 || year > currentYear + 1) {
      errs.year = `Year must be between 2000 and ${currentYear + 1}`;
    }

    if (!tankCapacity) {
      errs.tankCapacity = 'Tank capacity is required';
    } else if (Number(tankCapacity) <= 0) {
      errs.tankCapacity = 'Capacity must be greater than 0';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const payload = {
      license_plate: licensePlate.trim().toUpperCase(),
      make: make.trim(),
      model: model.trim(),
      year: Number(year),
      tank_capacity: Number(tankCapacity)
    };

    try {
      if (isEdit) {
        await updateVehicle(id, payload);
        success('Vehicle Updated', `Successfully updated profile for ${payload.license_plate}`);
      } else {
        await createVehicle(payload);
        success('Vehicle Created', `Successfully added new vehicle ${payload.license_plate}`);
      }
      navigate('/dashboard/vehicles');
    } catch (e) {
      error('Save Failed', e.message || 'An error occurred while saving.');
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
        title="Vehicle Profile Error"
        message="The vehicle details could not be loaded."
        onRetry={() => navigate('/dashboard/vehicles')}
      />
    );
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Title */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          icon={<ArrowLeft className="h-4 w-4" />}
          onClick={() => navigate('/dashboard/vehicles')}
        />
        <div>
          <h1 className="text-2xl font-bold text-content">
            {isEdit ? 'Edit Vehicle Profile' : 'Add New Vehicle'}
          </h1>
          <p className="text-sm text-content-secondary mt-0.5">
            {isEdit ? 'Update specifications and status parameters.' : 'Record a new truck in the logistics database.'}
          </p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="License Plate"
            placeholder="e.g. RJ14 XX 1234"
            value={licensePlate}
            onChange={(e) => setLicensePlate(e.target.value)}
            error={errors.licensePlate}
            required
            className="uppercase"
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Make / Manufacturer"
              placeholder="e.g. Tata Motors, Ashok Leyland"
              value={make}
              onChange={(e) => setMake(e.target.value)}
              error={errors.make}
              required
            />
            <Input
              label="Model"
              placeholder="e.g. Prima 4928.S, Signa 4825"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              error={errors.model}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Year of Manufacture"
              type="number"
              min="2000"
              max={new Date().getFullYear() + 1}
              value={year}
              onChange={(e) => setYear(e.target.value)}
              error={errors.year}
              required
            />
            <Input
              label="Fuel Tank Capacity (Liters)"
              type="number"
              min="1"
              value={tankCapacity}
              onChange={(e) => setTankCapacity(e.target.value)}
              error={errors.tankCapacity}
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/dashboard/vehicles')}
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
              Save Profile
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
