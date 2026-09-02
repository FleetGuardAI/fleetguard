import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Upload } from 'lucide-react';
import { createExpense } from '@/api/expenseApi';
import { getVehicles } from '@/api/vehicleApi';
import { getDrivers } from '@/api/driverApi';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input, Select } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { Loader } from '@/components/ui/Loader';
import { ErrorState } from '@/components/shared/ErrorState';
import { EXPENSE_CATEGORIES } from '@/utils/constants';

export default function ExpenseForm() {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [fetchError, setFetchError] = useState(null);

  // Form states
  const [vehicleId, setVehicleId] = useState('');
  const [driverId, setDriverId] = useState('');
  const [category, setCategory] = useState('');
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [uploadingFile, setUploadingFile] = useState(false);
  const [receiptUrl, setReceiptUrl] = useState('');

  const [errors, setErrors] = useState({});

  const loadResources = async () => {
    setFetching(true);
    setFetchError(null);
    try {
      const [vData, dData] = await Promise.all([
        getVehicles({ status: 'active' }),
        getDrivers({ status: 'active' })
      ]);
      setVehicles(vData);
      setDrivers(dData);
    } catch (e) {
      setFetchError(e);
      error('Load Error', 'Failed to retrieve active resources.');
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    loadResources();
  }, []);

  const validate = () => {
    const errs = {};
    if (!vehicleId) errs.vehicleId = 'Vehicle allocation is required';
    if (!driverId) errs.driverId = 'Driver identification is required';
    if (!category) errs.category = 'Expense category is required';
    if (!title.trim()) errs.title = 'Expense title/description is required';

    if (!amount) {
      errs.amount = 'Claim cost amount is required';
    } else if (Number(amount) <= 0) {
      errs.amount = 'Cost must be greater than 0';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const fileInputRef = React.useRef(null);
  const [ocrData, setOcrData] = useState(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingFile(true);
    setOcrData(null);
    try {
      const { uploadExpenseReceiptOCR } = await import('@/api/expenseApi');
      const response = await uploadExpenseReceiptOCR(file);
      
      // Assume the backend returns an object that can contain amount, vendor, date
      if (response.amount) {
        setAmount(response.amount.toString());
      }
      if (response.vendor) {
        setTitle(response.vendor);
      }
      
      setReceiptUrl(response.receipt_url || "uploaded"); // Assuming we don't have a direct URL immediately or we just mark it as uploaded
      setOcrData(response);
      success('Receipt Uploaded', 'OCR receipt processed successfully.');
    } catch (e) {
      error('Upload Failed', e.message || 'Failed to scan receipt.');
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);

    const selectedTruck = vehicles.find(v => v.id === Number(vehicleId));
    const selectedDriver = drivers.find(d => d.id === Number(driverId));

    const payload = {
      truck_id: selectedTruck?.id,
      driver_id: selectedDriver?.id,
      truck_plate: selectedTruck?.license_plate || '',
      driver_name: selectedDriver?.name || '',
      category,
      title: title.trim(),
      amount: Number(amount),
      receipt_url: receiptUrl
    };

    try {
      await createExpense(payload);
      success('Expense Claim Created', `Successfully logged expense for vehicle ${payload.truck_plate}.`);
      navigate('/dashboard/expenses');
    } catch (e) {
      error('Save Failed', e.message || 'Failed to submit expense claim.');
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
        message="Could not load vehicle or driver profiles to record expense."
        onRetry={loadResources}
      />
    );
  }

  const vehicleOptions = vehicles.map(v => ({ value: v.id, label: `${v.license_plate} - ${v.make} ${v.model}` }));
  const driverOptions = drivers.map(d => ({ value: d.id, label: d.name }));

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Title */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          icon={<ArrowLeft className="h-4 w-4" />}
          onClick={() => navigate('/dashboard/expenses')}
        />
        <div>
          <h1 className="text-2xl font-bold text-content">Submit Expense Claim</h1>
          <p className="text-sm text-content-secondary mt-0.5">Audit driver expense logs, OCR verified receipts, and check pricing anomalies.</p>
        </div>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Allocate Vehicle"
              placeholder="-- Select Truck --"
              options={vehicleOptions}
              value={vehicleId}
              onChange={(e) => setVehicleId(e.target.value)}
              error={errors.vehicleId}
              required
            />
            <Select
              label="Allocate Driver"
              placeholder="-- Select Operator --"
              options={driverOptions}
              value={driverId}
              onChange={(e) => setDriverId(e.target.value)}
              error={errors.driverId}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Expense Category"
              placeholder="-- Select Category --"
              options={EXPENSE_CATEGORIES}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              error={errors.category}
              required
            />
            <Input
              label="Claim Amount (INR)"
              type="number"
              min="1"
              placeholder="e.g. 1500"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              error={errors.amount}
              required
            />
          </div>

          <Input
            label="Claim Description Title"
            placeholder="e.g. Puncture repair near Pali highway dhaba"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            error={errors.title}
            required
          />

          {/* Receipt attachment */}
          <div className="space-y-1.5">
            <span className="block text-sm font-medium text-content-secondary">Scanned Bill Receipt Photo</span>
            <div className="flex items-center gap-3">
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept="image/*,.pdf"
                onChange={handleFileUpload}
              />
              <Button
                type="button"
                variant="outline"
                loading={uploadingFile}
                icon={<Upload className="h-4 w-4 text-brand-600" />}
                onClick={() => fileInputRef.current?.click()}
              >
                Scan Receipt Bill
              </Button>
              {receiptUrl ? (
                <span className="text-xs text-green-600 font-semibold">✓ Receipt attached successfully</span>
              ) : (
                <span className="text-xs text-content-secondary">No receipt attached</span>
              )}
            </div>
            {ocrData && ocrData.amount && (
               <div className="text-xs text-blue-600 mt-1">
                 Auto-populated amount: ₹{ocrData.amount} from {ocrData.vendor}
               </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-border">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/dashboard/expenses')}
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
              Log Expense
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
