import React, { useState, useEffect } from 'react';
import { Server, Plus, RefreshCw, CheckCircle2, AlertCircle, Trash2, Globe, Lock } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/components/ui/Toast';
import {
  getGPSProviders,
  createGPSProvider,
  testGPSProvider,
  syncGPSProvider,
  deleteGPSProvider,
} from '@/api/assetApi';

export default function ProviderManagementModal({ open, onClose }) {
  const { success, error: toastError } = useToast();

  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);

  // Form State
  const [providerType, setProviderType] = useState('TRACCAR');
  const [accountName, setAccountName] = useState('');
  const [serverUrl, setServerUrl] = useState('http://localhost:8082');
  const [apiToken, setApiToken] = useState('');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [syncInterval, setSyncInterval] = useState(60);
  const [saving, setSaving] = useState(false);

  // Per-card testing/syncing loading state
  const [actionLoading, setActionLoading] = useState({});

  const loadProviders = async () => {
    setLoading(true);
    try {
      const data = await getGPSProviders();
      setProviders(data || []);
    } catch (err) {
      console.error(err);
      toastError('Failed to load GPS providers', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      loadProviders();
      setShowAddForm(false);
    }
  }, [open]);

  const handleTest = async (id) => {
    setActionLoading(prev => ({ ...prev, [id]: 'testing' }));
    try {
      const res = await testGPSProvider(id);
      if (res.success || res.status === 'CONNECTED') {
        success('Provider Online', res.message || 'Successfully connected to server.');
      } else {
        toastError('Connection Failed', res.message || 'Unable to reach provider server.');
      }
      loadProviders();
    } catch (err) {
      toastError('Test Error', err.message);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: null }));
    }
  };

  const handleSync = async (id) => {
    setActionLoading(prev => ({ ...prev, [id]: 'syncing' }));
    try {
      const res = await syncGPSProvider(id);
      success('Sync Complete', res.message || 'Telemetry and devices synchronized.');
      loadProviders();
    } catch (err) {
      toastError('Sync Error', err.message);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: null }));
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to remove GPS provider "${name}"?`)) return;
    try {
      await deleteGPSProvider(id);
      success('Provider Removed', `Account "${name}" deleted.`);
      loadProviders();
    } catch (err) {
      toastError('Delete Failed', err.message);
    }
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const creds = apiToken.trim() || (password ? (username ? `${username.trim()}:${password}` : password) : undefined);
      await createGPSProvider({
        provider_type: providerType.toLowerCase(),
        name: accountName.trim(),
        server_url: serverUrl.trim() || undefined,
        credentials: creds,
        config: {
          sync_interval_seconds: parseInt(syncInterval, 10) || 60,
          username: username.trim() || undefined,
        },
      });
      success('Provider Added', `Integration "${accountName}" registered.`);
      setShowAddForm(false);
      setAccountName('');
      setPassword('');
      setApiToken('');
      loadProviders();
    } catch (err) {
      toastError('Failed to Add Provider', err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      size="lg"
      title="GPS Telematics Ingestion Engines & Providers"
      description="Manage Traccar servers, cloud telematics APIs, and forwarder integrations."
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-content uppercase tracking-wider">
            Connected Ingestion Servers ({providers.length})
          </span>
          {!showAddForm && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowAddForm(true)}
              icon={<Plus className="w-3.5 h-3.5" />}
            >
              Add Provider
            </Button>
          )}
        </div>

        {/* Add Provider Form */}
        {showAddForm && (
          <form onSubmit={handleAddSubmit} className="p-4 border border-brand-200 bg-brand-50/20 rounded-xl space-y-3">
            <h4 className="text-xs font-bold text-content flex items-center gap-2">
              <Server className="w-4 h-4 text-brand-600" />
              Configure Ingestion Server
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-content mb-1">Provider Type</label>
                <select
                  value={providerType}
                  onChange={(e) => setProviderType(e.target.value)}
                  className="w-full h-9 px-2.5 border border-border rounded-lg bg-surface text-content text-xs"
                >
                  <option value="TRACCAR">Traccar GPS Server (Recommended)</option>
                  <option value="TELTONIKA_FOTA">Teltonika Cloud API</option>
                  <option value="CONCOX_TRACKSOLID">Concox / Tracksolid</option>
                  <option value="GENERIC_REST">Generic Telematics REST API</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-content mb-1">Account Label</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Primary Traccar Instance"
                  value={accountName}
                  onChange={(e) => setAccountName(e.target.value)}
                  className="w-full h-9 px-2.5 border border-border rounded-lg bg-surface text-content text-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-content mb-1">Server Endpoint URL</label>
              <input
                type="text"
                required
                placeholder="http://localhost:8082 or https://traccar.yourfleet.com"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                className="w-full h-9 px-2.5 border border-border rounded-lg bg-surface text-content text-xs font-mono"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-content mb-1">API Token (Preferred)</label>
                <input
                  type="password"
                  placeholder="Bearer API Token"
                  value={apiToken}
                  onChange={(e) => setApiToken(e.target.value)}
                  className="w-full h-9 px-2.5 border border-border rounded-lg bg-surface text-content text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-content mb-1">Or Password (Basic Auth)</label>
                <input
                  type="password"
                  placeholder="Account password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-9 px-2.5 border border-border rounded-lg bg-surface text-content text-xs"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button size="sm" variant="ghost" type="button" onClick={() => setShowAddForm(false)}>
                Cancel
              </Button>
              <Button size="sm" variant="primary" type="submit" disabled={saving}>
                {saving ? 'Saving...' : 'Save Provider'}
              </Button>
            </div>
          </form>
        )}

        {/* Existing Providers List */}
        {loading ? (
          <div className="p-8 text-center text-xs text-content-muted">Loading providers...</div>
        ) : providers.length === 0 && !showAddForm ? (
          <div className="p-6 border border-dashed border-border rounded-xl text-center space-y-2">
            <Globe className="w-8 h-8 text-content-muted mx-auto" />
            <p className="text-xs font-medium text-content">No external GPS providers connected yet.</p>
            <p className="text-[11px] text-content-secondary max-w-sm mx-auto">
              You can connect a Traccar server or cloud telematics API to automatically synchronize live device positions and status.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {providers.map(p => {
              const displayName = p.name || p.account_name || 'Unnamed Provider';
              const status = p.sync_status || p.connection_status || 'UNKNOWN';
              const isHealthy = status === 'CONNECTED' || status === 'HEALTHY';
              const isError = status === 'ERROR' || status === 'FAILED';
              const lastSyncTime = p.last_sync_at || p.last_health_check_at;

              return (
                <div
                  key={p.id}
                  className="p-4 border border-border rounded-xl bg-surface flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-card"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-content">{displayName}</span>
                      <Badge variant="brand" size="sm">{p.provider_type?.toUpperCase()}</Badge>
                      <Badge variant={isHealthy ? 'success' : isError ? 'danger' : 'warning'} size="sm" dot>
                        {status}
                      </Badge>
                      {p.device_count !== undefined && (
                        <span className="text-[10px] text-content-muted font-medium">
                          {p.device_count} {p.device_count === 1 ? 'device' : 'devices'}
                        </span>
                      )}
                    </div>
                    {p.server_url && (
                      <p className="text-[11px] text-content-muted font-mono mt-0.5">{p.server_url}</p>
                    )}
                    {lastSyncTime && (
                      <p className="text-[10px] text-content-secondary mt-1">
                        Last sync: {new Date(lastSyncTime).toLocaleTimeString()}
                      </p>
                    )}
                    {p.sync_error && (
                      <p className="text-[10px] text-red-500 font-mono mt-0.5">{p.sync_error}</p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleTest(p.id)}
                      disabled={actionLoading[p.id] === 'testing'}
                      icon={<RefreshCw className={`w-3.5 h-3.5 ${actionLoading[p.id] === 'testing' ? 'animate-spin' : ''}`} />}
                    >
                      Test
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSync(p.id)}
                      disabled={actionLoading[p.id] === 'syncing'}
                      icon={<Server className="w-3.5 h-3.5" />}
                    >
                      Sync Devices
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDelete(p.id, displayName)}
                      className="text-red-500 hover:text-red-600 hover:bg-red-50"
                      icon={<Trash2 className="w-3.5 h-3.5" />}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="flex justify-end pt-3 border-t border-border">
          <Button variant="ghost" onClick={onClose}>Close</Button>
        </div>
      </div>
    </Modal>
  );
}
