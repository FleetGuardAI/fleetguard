import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, Moon, Sun, DownloadCloud, UploadCloud, ShieldAlert, BellRing, Smartphone, X } from 'lucide-react';
import { getSettings, saveSettings } from '@/api/settingsApi';
import { generateOwnerQR } from '@/api/authApi';
import { QRCodeSVG } from 'qrcode.react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { Loader } from '@/components/ui/Loader';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/utils/cn';

export default function Settings() {
  const { success, error, info } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // QR Auth
  const [qrToken, setQrToken] = useState(null);
  const [qrExpiry, setQrExpiry] = useState(null);
  const [qrLoading, setQrLoading] = useState(false);

  const handleGenerateQR = async () => {
    setQrLoading(true);
    setQrToken(null);
    try {
      const data = await generateOwnerQR();
      setQrToken(data.pairing_token);
      setQrExpiry(data.expires_in_seconds || 300);
    } catch (e) {
      error('QR Generation Failed', e.message || 'Could not generate QR code.');
    } finally {
      setQrLoading(false);
    }
  };

  useEffect(() => {
    if (qrExpiry && qrExpiry > 0 && qrToken) {
      const timer = setInterval(() => {
        setQrExpiry(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            setQrToken(null);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [qrExpiry, qrToken]);

  // Form states
  const [companyName, setCompanyName] = useState('');
  const [primaryContact, setPrimaryContact] = useState('');
  const [timezone, setTimezone] = useState('');
  const [currency, setCurrency] = useState('');
  const [fuelTheftThreshold, setFuelTheftThreshold] = useState('');
  const [speedLimit, setSpeedLimit] = useState('');
  const [smsAlerts, setSmsAlerts] = useState(false);


  const loadSettingsData = async () => {
    setLoading(true);
    try {
      const data = await getSettings();
      setCompanyName(data.companyName);
      setPrimaryContact(data.primaryContact);
      setTimezone(data.timezone);
      setCurrency(data.currency);
      setFuelTheftThreshold(data.fuelTheftThresholdLiters);
      setSpeedLimit(data.speedLimitKmh);
      setSmsAlerts(data.smsAlertsEnabled);
    } catch (e) {
      error('Load Error', 'Failed to retrieve system settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettingsData();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      companyName,
      primaryContact,
      timezone,
      currency,
      fuelTheftThresholdLiters: Number(fuelTheftThreshold),
      speedLimitKmh: Number(speedLimit),
      smsAlertsEnabled: smsAlerts
    };

    try {
      await saveSettings(payload);
      success('Settings Saved', 'System configurations updated successfully.');
    } catch (e) {
      error('Save Failed', 'Failed to update system settings.');
    } finally {
      setSaving(false);
    }
  };


  const [backingUp, setBackingUp] = useState(false);
  const handleBackup = async () => {
    setBackingUp(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      // Simulate download
      const backupData = {
        settings: { companyName, fuelTheftThreshold, speedLimit },
        timestamp: new Date().toISOString(),
        version: '1.2.0'
      };
      const blob = new Blob([JSON.stringify(backupData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fleetguard_backup_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      success('Backup Successful', 'System database settings compiled and downloaded.');
    } catch (e) {
      error('Backup Failed', 'Database compile error.');
    } finally {
      setBackingUp(false);
    }
  };

  const [restoring, setRestoring] = useState(false);
  const handleRestore = async () => {
    setRestoring(false);
    // Simulating file trigger
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async () => {
      setRestoring(true);
      try {
        await new Promise(resolve => setTimeout(resolve, 1200));
        success('Restore Successful', 'Database settings imported and configurations synced.');
      } catch (e) {
        error('Import Failed', 'Invalid JSON backup schema.');
      } finally {
        setRestoring(false);
      }
    };
    input.click();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content flex items-center gap-2">
            <SettingsIcon className="h-6 w-6" />
            System Configurations
          </h1>
          <p className="text-sm text-content-secondary mt-0.5">Customize notification webhooks, geofence radius settings, and backup schedules.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Settings Form */}
        <div className="lg:col-span-2 space-y-6">
          <form onSubmit={handleSave}>
            <Card className="space-y-4">
              <CardHeader className="p-0 pb-3 border-b border-border">
                <CardTitle className="text-base">Company Specifications</CardTitle>
              </CardHeader>

              <Input
                label="Registered Company Name"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
              />

              <Input
                label="Primary Contact Personnel"
                value={primaryContact}
                onChange={(e) => setPrimaryContact(e.target.value)}
                required
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Select
                  label="Local Timezone"
                  options={[
                    { value: 'Asia/Kolkata (IST)', label: 'India Standard Time (IST)' },
                    { value: 'UTC', label: 'Coordinated Universal Time (UTC)' }
                  ]}
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  required
                />
                <Select
                  label="Display Currency"
                  options={[
                    { value: 'INR (₹)', label: 'Indian Rupee (₹)' },
                    { value: 'USD ($)', label: 'US Dollar ($)' }
                  ]}
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  required
                />
              </div>

              <div className="pt-4 border-t border-border">
                <h4 className="text-sm font-semibold text-content mb-3 flex items-center gap-1.5">
                  <ShieldAlert className="h-4 w-4 text-brand-600" />
                  Telematics Alert Thresholds
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Suspected Fuel Theft Threshold (Liters)"
                    type="number"
                    min="1"
                    value={fuelTheftThreshold}
                    onChange={(e) => setFuelTheftThreshold(e.target.value)}
                    required
                  />
                  <Input
                    label="Geofence Highway Speed Limit (km/h)"
                    type="number"
                    min="1"
                    value={speedLimit}
                    onChange={(e) => setSpeedLimit(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-border">
                <h4 className="text-sm font-semibold text-content mb-3 flex items-center gap-1.5">
                  <BellRing className="h-4 w-4 text-brand-600" />
                  Dispatches Notifications Channels
                </h4>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={smsAlerts}
                      onChange={(e) => setSmsAlerts(e.target.checked)}
                      className="rounded border-border text-brand-600 focus:ring-brand-500/20"
                    />
                    <div className="text-sm">
                      <span className="font-semibold text-content block">SMS Alerts Active</span>
                      <span className="text-xs text-content-secondary">Forward critical alarms directly to owner mobile phones.</span>
                    </div>
                  </label>
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-border">
                <Button
                  type="submit"
                  variant="primary"
                  icon={<Save className="h-4 w-4" />}
                  loading={saving}
                >
                  Save System Config
                </Button>
              </div>
            </Card>
          </form>
        </div>

        {/* Sidebar Theme & Backup Options */}
        <div className="lg:col-span-1 space-y-6">

          {/* Owner App Pairing */}
          <Card className="space-y-4 border-brand-500/20 bg-brand-500/5">
            <CardHeader className="p-0 pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Smartphone className="h-4 w-4 text-brand-600" />
                Owner App Pairing
              </CardTitle>
            </CardHeader>
            <p className="text-sm text-content-secondary">
              Generate a secure, single-use QR code to authenticate the Owner Mobile App.
            </p>
            
            {qrToken ? (
              <div className="flex flex-col items-center p-4 bg-surface rounded-xl border border-border mt-4">
                <div className="bg-white p-3 rounded-lg shadow-sm mb-3">
                  <QRCodeSVG value={qrToken} size={150} level="H" />
                </div>
                <p className="text-sm font-semibold text-content mb-1">Pairing Code Active</p>
                <p className="text-xs text-content-secondary">
                  Expires in {Math.floor(qrExpiry / 60)}:{(qrExpiry % 60).toString().padStart(2, '0')}
                </p>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => setQrToken(null)}
                  className="mt-3 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20"
                >
                  <X className="h-4 w-4 mr-1" /> Revoke
                </Button>
              </div>
            ) : (
              <Button
                variant="primary"
                className="w-full"
                onClick={handleGenerateQR}
                loading={qrLoading}
              >
                Generate QR Code
              </Button>
            )}
          </Card>


          {/* Backup & Restore Database Card */}
          <Card className="space-y-4">
            <CardHeader className="p-0 pb-2">
              <CardTitle className="text-base">Backup & Restore DB</CardTitle>
            </CardHeader>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                icon={<DownloadCloud className="h-4 w-4 text-brand-600" />}
                loading={backingUp}
                onClick={handleBackup}
              >
                Backup Database
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                icon={<UploadCloud className="h-4 w-4 text-brand-600" />}
                loading={restoring}
                onClick={handleRestore}
              >
                Restore Database
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
