import React, { useState, useEffect } from 'react';
import { Users, Plus, ShieldCheck, Mail, ToggleLeft, ToggleRight, Trash2, ShieldAlert, QrCode, UserPlus, Smartphone, Laptop, TabletSmartphone } from 'lucide-react';
import { getAdminUsers, addAdminUser, toggleAdminUserStatus } from '@/api/settingsApi';
import { Table } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SearchBox } from '@/components/shared/SearchBox';
import { Pagination } from '@/components/ui/Pagination';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/shared/ErrorState';
import { EmptyState } from '@/components/shared/EmptyState';
import { useToast } from '@/components/ui/Toast';
import { usePagination } from '@/hooks/usePagination';
import { Modal } from '@/components/ui/Modal';
import { Input, Select } from '@/components/ui/Input';
import { Dropdown } from '@/components/ui/Dropdown';
import { cn } from '@/utils/cn';

export default function UserManagement() {
  const { success, error, info } = useToast();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  // Filters
  const [search, setSearch] = useState('');

  // Modals
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [qrModalOpen, setQrModalOpen] = useState(false);
  const [qrScanning, setQrScanning] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('Dispatcher');
  const [department, setDepartment] = useState('Logistics');
  const [formErrors, setFormErrors] = useState({});

  const loadUsers = async () => {
    setLoading(true);
    setErr(null);
    try {
      const data = await getAdminUsers();
      // Apply client-side search since we have local state
      let filtered = [...data];
      if (search) {
        const q = search.toLowerCase();
        filtered = filtered.filter(u =>
          u.name.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q) ||
          u.role.toLowerCase().includes(q)
        );
      }
      setUsers(filtered);
    } catch (e) {
      setErr(e);
      error('Load Error', 'Failed to retrieve admin users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [search]);

  // Pagination
  const {
    page,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    changePageSize
  } = usePagination({ totalItems: users.length, initialPageSize: 10 });

  const paginatedUsers = users.slice(startIndex, endIndex);

  const validateForm = () => {
    const errs = {};
    if (!name.trim()) errs.name = 'Full name is required';
    if (!email.trim()) {
      errs.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errs.email = 'Invalid email address format';
    }

    setFormErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setSubmitting(true);
    const payload = {
      name: name.trim(),
      email: email.trim().toLowerCase(),
      role,
      department
    };

    try {
      const newUser = await addAdminUser(payload);
      setUsers(prev => [...prev, newUser]);
      success('User Created', `Successfully invited ${payload.name} as ${payload.role}.`);
      setAddModalOpen(false);
      setName('');
      setEmail('');
    } catch (e) {
      error('Action Failed', 'Failed to create user invitation.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSimulateQrScan = () => {
    error('Action Unavailable', 'Simulation is disabled in production. Please use a real mobile device to scan.');
  };

  const handleToggleStatus = async (id, userName, currentStatus) => {
    try {
      const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
      const updated = await toggleAdminUserStatus(id, newStatus);
      setUsers(prev => prev.map(u => u.id === id ? { ...u, status: updated.status } : u));
      success('Status Updated', `Successfully updated active status for ${userName}.`);
    } catch (e) {
      error('Action Failed', 'Failed to toggle status.');
    }
  };

  const columns = [
    {
      key: 'name',
      label: 'Full Name',
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center font-bold text-xs">
            {item.name.split(' ').map(n => n[0]).join('')}
          </div>
          <span className="font-semibold text-content">{item.name}</span>
        </div>
      )
    },
    {
      key: 'email',
      label: 'Email Address'
    },
    {
      key: 'role',
      label: 'Role Badge',
      render: (item) => <Badge variant="brand">{item.role}</Badge>
    },
    {
      key: 'department',
      label: 'Department'
    },
    {
      key: 'platform',
      label: 'Platform',
      render: (item) => (
        <div className="flex items-center gap-2">
          {item.platform === 'Mobile User' && <Smartphone className="h-4 w-4 text-brand-600" title="Mobile User" />}
          {item.platform === 'PC User' && <Laptop className="h-4 w-4 text-blue-600" title="PC User" />}
          {item.platform === 'Both' && <TabletSmartphone className="h-4 w-4 text-amber-600" title="Both PC & Mobile" />}
          <span className="text-sm font-medium text-content-secondary">{item.platform || 'PC User'}</span>
        </div>
      )
    },
    {
      key: 'status',
      label: 'Access Status',
      render: (item) => (
        <Badge variant={item.status === 'active' ? 'success' : 'neutral'} dot>
          {item.status.toUpperCase()}
        </Badge>
      )
    },
    {
      key: 'actions',
      label: 'Toggle Active Status',
      className: 'text-right',
      render: (item) => (
        <div className="flex justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            className={item.status === 'active' ? 'text-green-600' : 'text-content-muted'}
            icon={item.status === 'active' ? <ToggleRight className="h-6 w-6" /> : <ToggleLeft className="h-6 w-6" />}
            onClick={() => handleToggleStatus(item.id, item.name, item.status)}
            title={item.status === 'active' ? 'Deactivate User' : 'Activate User'}
          />
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-content flex items-center gap-2">
            <Users className="h-6 w-6" />
            System Users
          </h1>
          <p className="text-sm text-content-secondary mt-0.5">Manage dashboard access, assign departments, and invite app users.</p>
        </div>
        <Dropdown
          align="right"
          trigger={
            <Button variant="primary" icon={<Plus className="h-4 w-4" />}>
              Add Team User
            </Button>
          }
          items={[
            {
              label: 'Scan QR Code (Mobile App)',
              icon: <QrCode className="h-4 w-4" />,
              onClick: () => setQrModalOpen(true)
            },
            {
              label: 'Add User Manually',
              icon: <UserPlus className="h-4 w-4" />,
              onClick: () => setAddModalOpen(true)
            }
          ]}
        />
      </div>

      {/* Filters Card */}
      <Card className="p-4 flex items-center justify-between">
        <SearchBox
          value={search}
          onChange={setSearch}
          placeholder="Search team member name, email..."
          className="w-full md:max-w-xs"
        />
      </Card>

      {/* Main Table */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="p-6">
            <SkeletonTable rows={5} cols={6} />
          </div>
        ) : err ? (
          <ErrorState
            title="Failed to Load Co-users"
            message={err.message || 'An error occurred.'}
            onRetry={loadUsers}
          />
        ) : users.length === 0 ? (
          <EmptyState
            title="No Team Members Found"
            description="There are no co-users matching the current filters."
            actionLabel="Add Team User"
            onAction={() => setAddModalOpen(true)}
          />
        ) : (
          <>
            <Table
              columns={columns}
              data={paginatedUsers}
              keyExtractor={(item) => item.id}
            />
            <div className="border-t border-border px-6">
              <Pagination
                page={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={users.length}
                onPageChange={goToPage}
                onPageSizeChange={changePageSize}
              />
            </div>
          </>
        )}
      </Card>

      {/* Add User Modal */}
      <Modal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        title="Add Co-Admin User"
        description="Invite a new operations team member to access FleetGuard."
        closable={!submitting}
        footer={
          <>
            <Button variant="outline" onClick={() => setAddModalOpen(false)} disabled={submitting}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleAddUser} loading={submitting}>
              Invite Member
            </Button>
          </>
        }
      >
        <form className="space-y-4" onSubmit={handleAddUser}>
          <Input
            label="Full Name"
            placeholder="e.g. Suryansh Chaudhary"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={formErrors.name}
            required
          />

          <Input
            label="Corporate Email Address"
            placeholder="e.g. suryansh@fleetguard.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={formErrors.email}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Assigned System Role"
              options={[
                { value: 'COO', label: 'Chief Operations Officer (COO)' },
                { value: 'Fleet Manager', label: 'Fleet Manager' },
                { value: 'Dispatcher', label: 'Route Dispatcher' },
                { value: 'Finance Admin', label: 'Finance Auditor' }
              ]}
              value={role}
              onChange={(e) => setRole(e.target.value)}
              required
            />
            <Select
              label="Department Allocation"
              options={[
                { value: 'Operations', label: 'Executive Operations' },
                { value: 'Maintenance', label: 'Maintenance & Spares' },
                { value: 'Logistics', label: 'Route Dispatches' },
                { value: 'Finance', label: 'Finance & Payments' }
              ]}
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              required
            />
          </div>
        </form>
      </Modal>

      {/* QR Code Invitation Modal */}
      <Modal
        open={qrModalOpen}
        onClose={() => setQrModalOpen(false)}
        title="Owner App Invite QR Code"
        description="Ask the user to scan this unique QR code with their mobile device to instantly join the workspace."
        footer={
          <div className="w-full flex justify-end items-center">
            <Button variant="outline" onClick={() => setQrModalOpen(false)} disabled={qrScanning}>
              Close
            </Button>
          </div>
        }
      >
        <div className="flex flex-col items-center justify-center py-6 space-y-6">
          <div className="p-4 bg-white rounded-2xl shadow-sm border border-border">
            <div className="w-48 h-48 bg-gradient-to-br from-brand-100 to-brand-50 flex items-center justify-center rounded-xl border-2 border-brand-200 border-dashed relative">
              <QrCode className="w-24 h-24 text-brand-600 opacity-60" />
              <div className="absolute inset-0 flex items-center justify-center">
                 <div className="w-10 h-10 bg-white rounded-lg shadow-sm flex items-center justify-center">
                   <img src="/assets/fleetguard-logo.png" alt="FG" className="w-6 h-6 object-contain" />
                 </div>
              </div>
            </div>
          </div>
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-content">Workspace ID: FG-WORKSPACE-843</p>
            <p className="text-xs text-content-muted max-w-[250px] mx-auto">
              Scanning this code binds the user's mobile app to your dashboard instantly.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
