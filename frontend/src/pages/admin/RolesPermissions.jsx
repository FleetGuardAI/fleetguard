import React, { useState, useEffect } from 'react';
import { ShieldAlert, Save, Shield, Settings, Key, HelpCircle } from 'lucide-react';
import { getRolesMatrix, updateRolePermissions } from '@/api/settingsApi';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Loader } from '@/components/ui/Loader';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/utils/cn';

export default function RolesPermissions() {
  const { success, error } = useToast();

  const [roles, setRoles] = useState([]);
  const [selectedRoleName, setSelectedRoleName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Current selected role permissions state
  const [permissions, setPermissions] = useState({});

  const loadMatrix = async () => {
    setLoading(true);
    try {
      const data = await getRolesMatrix();
      setRoles(data);
      if (data.length > 0) {
        setSelectedRoleName(data[0].role);
        setPermissions(data[0].permissions);
      }
    } catch (e) {
      error('Load Error', 'Failed to retrieve permissions matrix.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMatrix();
  }, []);

  const handleRoleSelect = (roleName) => {
    setSelectedRoleName(roleName);
    const target = roles.find(r => r.role === roleName);
    if (target) {
      setPermissions(target.permissions);
    }
  };

  const handlePermissionChange = (module, action, checked) => {
    setPermissions(prev => {
      const currentActions = prev[module] || [];
      const updatedActions = checked
        ? [...currentActions, action]
        : currentActions.filter(a => a !== action);
      
      return {
        ...prev,
        [module]: updatedActions
      };
    });
  };

  const handleSaveMatrix = async () => {
    setSaving(true);
    try {
      await updateRolePermissions(selectedRoleName, permissions);
      // Update local state roles
      setRoles(prev => prev.map(r => r.role === selectedRoleName ? { ...r, permissions } : r));
      success('Matrix Updated', `Permissions for role ${selectedRoleName} saved successfully.`);
    } catch (e) {
      error('Save Failed', 'Failed to update permissions matrix.');
    } finally {
      setSaving(false);
    }
  };

  const modules = [
    { key: 'dashboard', label: 'Overview Dashboard' },
    { key: 'vehicles', label: 'Vehicles Module' },
    { key: 'drivers', label: 'Drivers Registry' },
    { key: 'trips', label: 'Trips & Dispatch' },
    { key: 'fuel', label: 'Fuel Logs & Telematics' },
    { key: 'expenses', label: 'Expenses Claims' },
    { key: 'payments', label: 'Payments & Vendors' },
    { key: 'maintenance', label: 'Maintenance Logs' },
    { key: 'documents', label: 'Documents Repository' },
    { key: 'system', label: 'System Settings' }
  ];

  const actions = [
    { key: 'view', label: 'Read / View' },
    { key: 'create', label: 'Write / Create' },
    { key: 'edit', label: 'Modify / Edit' },
    { key: 'delete', label: 'Archive / Delete' }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader size="lg" />
      </div>
    );
  }

  const selectedRole = roles.find(r => r.role === selectedRoleName);

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content flex items-center gap-2">
            <Shield className="h-6 w-6" />
            Roles & Permissions Matrix
          </h1>
          <p className="text-sm text-content-secondary mt-0.5">Customize operational capabilities, disable actions, and secure company assets.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Role list sidebar */}
        <div className="lg:col-span-1 space-y-3">
          <span className="text-xs font-bold text-content-secondary uppercase tracking-wider block">System Roles</span>
          {roles.map((r) => (
            <button
              key={r.role}
              onClick={() => handleRoleSelect(r.role)}
              className={cn(
                "w-full text-left p-4 rounded-xl border transition-all duration-200",
                selectedRoleName === r.role
                  ? "border-brand-600 bg-brand-50/20 text-brand-600 dark:border-brand-500 dark:text-brand-500"
                  : "border-border text-content hover:bg-slate-50 dark:hover:bg-slate-800/40"
              )}
            >
              <span className="font-semibold block">{r.role}</span>
              <span className="text-xs text-content-secondary mt-1 block leading-normal">{r.description}</span>
            </button>
          ))}
        </div>

        {/* Matrix Grid */}
        <Card className="lg:col-span-3 space-y-6">
          <div className="flex justify-between items-center border-b border-border pb-3">
            <div>
              <h2 className="text-lg font-bold text-content">{selectedRoleName} Permissions</h2>
              <p className="text-xs text-content-secondary mt-0.5">Fine-tune read/write controls for operational modules.</p>
            </div>
            <Button
              variant="primary"
              icon={<Save className="h-4 w-4" />}
              loading={saving}
              onClick={handleSaveMatrix}
            >
              Save Matrix Changes
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="pb-3 text-xs font-bold text-content-secondary uppercase w-1/3">Module / Feature Section</th>
                  {actions.map(act => (
                    <th key={act.key} className="pb-3 text-xs font-bold text-content-secondary uppercase text-center w-1/6">
                      {act.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {modules.map((mod) => (
                  <tr key={mod.key} className="border-b border-border hover:bg-slate-50/50 dark:hover:bg-slate-800/10">
                    <td className="py-4">
                      <span className="text-sm font-semibold text-content block">{mod.label}</span>
                      <span className="text-[10px] text-content-muted font-mono block mt-0.5">{mod.key}</span>
                    </td>
                    {actions.map((act) => {
                      const hasPerm = (permissions[mod.key] || []).includes(act.key);
                      return (
                        <td key={act.key} className="py-4 text-center">
                          <input
                            type="checkbox"
                            checked={hasPerm}
                            onChange={(e) => handlePermissionChange(mod.key, act.key, e.target.checked)}
                            className="rounded border-border text-brand-600 focus:ring-brand-500/20 h-4 w-4 cursor-pointer"
                          />
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-4 bg-slate-50 dark:bg-slate-800/40 border border-border rounded-xl flex gap-3 text-xs text-content-secondary">
            <HelpCircle className="h-5 w-5 text-brand-600 flex-shrink-0" />
            <p className="leading-relaxed">
              Permissions modifications apply instantly to all co-users assigned to this role. Revoking view permissions will hide sidebar navigation items.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
