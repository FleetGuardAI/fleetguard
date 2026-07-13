import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { getDriverById, createDriver, updateDriver } from '@/api/driverApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';

export default function DriverForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { success, error } = useToast();

  const isEdit = Boolean(id);

  const [name, setName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);
  const [fetchError, setFetchError] = useState(null);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (isEdit) {
      const fetchDriver = async () => {
        setFetching(true);
        setFetchError(null);
        try {
          const d = await getDriverById(id);
          setName(d.name);
          setPhoneNumber(d.phone_number);
        } catch (e) {
          setFetchError(e);
          error('Load Failed', 'Could not retrieve driver profile details.');
        } finally {
          setFetching(false);
        }
      };
      fetchDriver();
    }
  }, [id, isEdit]);

  const validate = () => {
    const errs = {};
    if (!name.trim()) errs.name = 'Driver name is required';

    if (!phoneNumber.trim()) {
      errs.phoneNumber = 'Phone number is required';
    } else if (!/^(\+91)?[0-9]{10}$/.test(phoneNumber.trim().replace(/[\s\-]/g, ''))) {
      errs.phoneNumber = 'Invalid mobile number. Must contain 10 digits (e.g. +919876543210)';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    let cleanedPhone = phoneNumber.trim().replace(/[\s\-]/g, '');
    if (!cleanedPhone.startsWith('+91') && cleanedPhone.length === 10) {
      cleanedPhone = '+91' + cleanedPhone;
    }

    const payload = {
      name: name.trim(),
      phone_number: cleanedPhone
    };

    try {
      if (isEdit) {
        await updateDriver(id, payload);
        success('Driver Updated', `Successfully updated profile for ${payload.name}`);
      } else {
        await createDriver(payload);
        success('Driver Profile Created', `Successfully added operator ${payload.name}`);
      }
      navigate('/dashboard/drivers');
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
        title="Driver Profile Error"
        message="The driver credentials could not be loaded."
        onRetry={() => navigate('/dashboard/drivers')}
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
          onClick={() => navigate('/dashboard/drivers')}
        />
        <div>
          <h1 className="text-2xl font-bold text-content">
            {isEdit ? 'Edit Driver Profile' : 'Add New Driver'}
          </h1>
          <p className="text-sm text-content-secondary mt-0.5">
            {isEdit ? 'Modify phone settings and operators details.' : 'Register a new commercial truck operator.'}
          </p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Driver Name"
            placeholder="e.g. Rajesh Kumar"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={errors.name}
            required
          />

          <Input
            label="WhatsApp / Mobile Phone"
            placeholder="e.g. +919876543210"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            error={errors.phoneNumber}
            required
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/dashboard/drivers')}
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
