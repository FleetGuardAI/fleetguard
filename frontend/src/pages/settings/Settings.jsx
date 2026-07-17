import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, Moon, Sun, DownloadCloud, UploadCloud, ShieldAlert, BellRing } from 'lucide-react';
import { getSettings, saveSettings } from '@/api/settingsApi';
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

  // Form states
  const [companyName, setCompanyName] = useState('');
  const [primaryContact, setPrimaryContact] = useState('');
  const [timezone, setTimezone] = useState('');
  const [currency, setCurrency] = useState('');
  const [fuelTheftThreshold, setFuelTheftThreshold] = useState('');
  const [speedLimit, setSpeedLimit] = useState('');
  const [smsAlerts, setSmsAlerts] = useState(false);
  const [whatsappBot, setWhatsappBot] = useState(false);

  // Theme state
  const [themeMode, setThemeMode] = useState(() => {
    return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
  });

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
      setWhatsappBot(data.whatsappBotActive);
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
      smsAlertsEnabled: smsAlerts,
      whatsappBotActive: whatsappBot
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

  const handleThemeChange = (mode) => {
    setThemeMode(mode);
    const root = document.documentElement;
    if (mode === 'dark') {
      root.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
    success('Theme Updated', `Switched workspace theme to ${mode.toUpperCase()} mode.`);
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
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={whatsappBot}
                      onChange={(e) => setWhatsappBot(e.target.checked)}
                      className="rounded border-border text-brand-600 focus:ring-brand-500/20"
                    />
                    <div className="text-sm">
                      <span className="font-semibold text-content block">WhatsApp Bot integration</span>
                      <span className="text-xs text-content-secondary">Allow driver expense submissions directly via WhatsApp OCR bot.</span>
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
          {/* Theme Workspace Card */}
          <Card className="space-y-4">
            <CardHeader className="p-0 pb-2">
              <CardTitle className="text-base">Workspace Theme settings</CardTitle>
            </CardHeader>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleThemeChange('light')}
                className={cn(
                  "p-3 rounded-xl border flex flex-col items-center justify-center gap-2 transition-all font-semibold text-sm",
                  themeMode === 'light'
                    ? "border-brand-600 bg-brand-50/20 text-brand-600"
                    : "border-border text-content-secondary hover:text-content hover:bg-slate-50"
                )}
              >
                <Sun className="h-5 w-5" />
                Light Mode
              </button>
              <button
                type="button"
                onClick={() => handleThemeChange('dark')}
                className={cn(
                  "p-3 rounded-xl border flex flex-col items-center justify-center gap-2 transition-all font-semibold text-sm",
                  themeMode === 'dark'
                    ? "border-brand-500 bg-brand-950/20 text-brand-500"
                    : "border-border text-content-secondary hover:text-content hover:bg-slate-50"
                )}
              >
                <Moon className="h-5 w-5" />
                Dark Mode
              </button>
            </div>
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
